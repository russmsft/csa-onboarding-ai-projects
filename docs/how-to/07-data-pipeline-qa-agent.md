# 07 — Data Pipeline QA Agent: Catch Data Quality Issues Automatically

Your data pipeline finished. Did it produce good data? This guide builds an Azure Functions trigger that runs statistical anomaly detection on pipeline output and fires an alert when something looks wrong.

---

## What You're Building

An Azure Function triggered by an Event Grid pipeline-completion event. The function collects run stats (row count, null rates, schema) and sends them to a Foundry agent with Code Interpreter. The agent runs Python-based anomaly detection against historical baselines, generates a QA report, and calls a function to raise an alert if anomalies exceed thresholds. Uses GPT-4.1-mini + Code Interpreter — cheap and effective for statistical work.

---

## Prerequisites

- Microsoft Foundry project with GPT-4.1-mini deployed
- Azure Data Factory or Synapse pipeline (as the event source)
- Azure Event Grid subscription on the pipeline completion event
- Azure Storage Account for baseline stats history
- Python 3.11+, `azure-functions`, `azure-ai-projects`, `azure-storage-blob`

```bash
pip install azure-ai-projects azure-identity azure-functions \
  azure-storage-blob azure-eventgrid python-dotenv
```

---

## Architecture

![Data Pipeline QA architecture: ADF/Synapse pipeline → Event Grid → Azure Function → Blob Storage baselines → Foundry Agent GPT-4.1-mini with Code Interpreter → QA report and alert](images/07-data-pipeline-qa-agent-architecture.png)

---

## Step-by-Step Build

### Step 1 — Create the Event Grid subscription

```bash
# Subscribe to ADF pipeline run completion events
PIPELINE_ID=$(az datafactory pipeline list \
  --resource-group $RG \
  --factory-name $ADF_NAME \
  --query "[0].id" -o tsv)

az eventgrid event-subscription create \
  --name pipeline-qa-trigger \
  --source-resource-id /subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.DataFactory/factories/$ADF_NAME \
  --endpoint-type azurefunction \
  --endpoint /subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Web/sites/$FUNC_APP/functions/pipeline_qa_trigger \
  --included-event-types Microsoft.DataFactory.PipelineRunCompleted
```

### Step 2 — Azure Function definition

```python
# function_app.py
import os
import json
import logging
from datetime import datetime, timezone
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

app = func.FunctionApp()
logger = logging.getLogger(__name__)

credential = DefaultAzureCredential()
blob_client = BlobServiceClient(
    account_url=f"https://{os.environ['STORAGE_ACCOUNT']}.blob.core.windows.net",
    credential=credential
)
ai_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=credential
)


@app.event_grid_trigger(arg_name="event")
def pipeline_qa_trigger(event: func.EventGridEvent):
    """Triggered when an ADF pipeline run completes."""
    data = event.get_json()
    logger.info(f"Pipeline event: {json.dumps(data)}")

    pipeline_name = data.get("pipelineName", "unknown")
    run_id = data.get("runId", "unknown")
    status = data.get("status", "unknown")

    if status != "Succeeded":
        logger.info(f"Pipeline {pipeline_name} did not succeed (status={status}), skipping QA.")
        return

    # Collect pipeline run stats
    stats = collect_pipeline_stats(pipeline_name, run_id, data)
    logger.info(f"Stats collected: {json.dumps(stats)}")

    # Load historical baseline
    baseline = load_baseline(pipeline_name)

    # Run QA analysis
    agent_id = os.environ.get("QA_AGENT_ID") or create_qa_agent()
    report = run_qa_analysis(agent_id, pipeline_name, stats, baseline)

    # Save updated baseline
    save_baseline(pipeline_name, stats)

    # Log report
    logger.info(f"QA Report for {pipeline_name}:\n{report}")
```

### Step 3 — Collect stats from the pipeline run

```python
def collect_pipeline_stats(
    pipeline_name: str,
    run_id: str,
    event_data: dict
) -> dict:
    """
    In production: query ADF API or Synapse output tables.
    Here we extract from the event payload and ADF activity outputs.
    """
    # These come from the Event Grid event data
    return {
        "pipeline_name": pipeline_name,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": event_data.get("durationInMs", 0) / 1000,
        "rows_read": event_data.get("output", {}).get("rowsRead", 0),
        "rows_written": event_data.get("output", {}).get("rowsWritten", 0),
        "tables": event_data.get("output", {}).get("tables", []),
        # In production, compute these from the actual output data:
        "null_rates": event_data.get("output", {}).get("nullRates", {}),
        "schema_hash": event_data.get("output", {}).get("schemaHash", ""),
    }
```

### Step 4 — Baseline storage helpers

```python
BASELINE_CONTAINER = "pipeline-baselines"

def load_baseline(pipeline_name: str) -> dict | None:
    """Load historical stats baseline from blob storage."""
    blob_name = f"{pipeline_name}/baseline.json"
    try:
        blob = blob_client.get_blob_client(
            container=BASELINE_CONTAINER,
            blob=blob_name
        )
        data = blob.download_blob().readall()
        return json.loads(data)
    except Exception:
        logger.info(f"No baseline found for {pipeline_name} — first run.")
        return None


def save_baseline(pipeline_name: str, stats: dict):
    """Update baseline with latest run stats (rolling average)."""
    existing = load_baseline(pipeline_name) or {
        "run_count": 0,
        "avg_rows_written": 0,
        "avg_duration_seconds": 0,
        "schema_hash": stats.get("schema_hash", ""),
        "null_rate_history": {}
    }

    n = existing["run_count"]
    existing["run_count"] = n + 1
    existing["avg_rows_written"] = (
        (existing["avg_rows_written"] * n + stats["rows_written"]) / (n + 1)
    )
    existing["avg_duration_seconds"] = (
        (existing["avg_duration_seconds"] * n + stats["duration_seconds"]) / (n + 1)
    )
    existing["schema_hash"] = stats.get("schema_hash", existing["schema_hash"])

    blob = blob_client.get_blob_client(
        container=BASELINE_CONTAINER,
        blob=f"{pipeline_name}/baseline.json"
    )
    blob.upload_blob(
        json.dumps(existing, indent=2),
        overwrite=True
    )
```

### Step 5 — Create the QA agent with Code Interpreter

```python
from azure.ai.projects.models import (
    CodeInterpreterTool, FunctionTool, PromptAgentDefinition, MessageRole,
    SubmitToolOutputsAction
)
import time

ALERT_TOOL_DEF = {
    "name": "send_alert",
    "description": "Send a data quality alert when anomalies exceed thresholds.",
    "parameters": {
        "type": "object",
        "properties": {
            "severity": {"type": "string", "enum": ["critical", "warning", "info"]},
            "anomaly_type": {"type": "string"},
            "pipeline_name": {"type": "string"},
            "details": {"type": "string"}
        },
        "required": ["severity", "anomaly_type", "pipeline_name", "details"]
    }
}


def send_alert(severity: str, anomaly_type: str, pipeline_name: str, details: str) -> str:
    """Real alert: POST to Teams webhook or Azure Monitor."""
    webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if webhook_url:
        import urllib.request
        payload = json.dumps({
            "@type": "MessageCard",
            "summary": f"Data Quality Alert: {pipeline_name}",
            "themeColor": "FF0000" if severity == "critical" else "FFA500",
            "sections": [{
                "activityTitle": f"[{severity.upper()}] {anomaly_type}",
                "activityText": f"Pipeline: **{pipeline_name}**\n\n{details}"
            }]
        }).encode()
        req = urllib.request.Request(webhook_url, data=payload,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
    logger.warning(f"ALERT [{severity}] {pipeline_name}: {anomaly_type} — {details}")
    return json.dumps({"sent": True, "severity": severity})


def create_qa_agent() -> str:
    code_interpreter = CodeInterpreterTool()
    alert_tool = FunctionTool(functions=[ALERT_TOOL_DEF])

    agent_def = PromptAgentDefinition(
        model="gpt-4.1-mini",
        name="pipeline-qa-agent",
        instructions=(
            "You are a data pipeline QA analyst. Given current run statistics and "
            "historical baseline, perform anomaly detection.\n\n"
            "Use Code Interpreter to run these checks in Python:\n"
            "1. Row count deviation: flag if >20% from baseline average\n"
            "2. Null rate spike: flag if any column null rate increased >5 percentage points\n"
            "3. Schema drift: flag if schema hash differs from baseline\n"
            "4. Duration anomaly: flag if run took >50% longer than baseline average\n\n"
            "Compute z-scores for row count and duration. "
            "Generate a QA report as markdown.\n\n"
            "If any check fails with severity WARNING or higher, call send_alert()."
        ),
        tools=[code_interpreter.definitions, *alert_tool.definitions],
        tool_resources=code_interpreter.resources,
    )
    agent = ai_client.agents.create_version(definition=agent_def)
    return agent.id


def run_qa_analysis(agent_id: str, pipeline_name: str, stats: dict, baseline: dict | None) -> str:
    thread = ai_client.agents.create_thread()
    ai_client.agents.create_message(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=(
            f"Run QA analysis for pipeline: **{pipeline_name}**\n\n"
            f"Current run stats:\n```json\n{json.dumps(stats, indent=2)}\n```\n\n"
            f"Historical baseline:\n```json\n{json.dumps(baseline or {}, indent=2)}\n```\n\n"
            "Generate a QA report and alert on any anomalies."
        )
    )

    run = ai_client.agents.create_run(thread_id=thread.id, agent_id=agent_id)

    while run.status in ("queued", "in_progress", "requires_action"):
        time.sleep(1)
        run = ai_client.agents.get_run(thread_id=thread.id, run_id=run.id)

        if run.status == "requires_action":
            action = run.required_action
            if isinstance(action, SubmitToolOutputsAction):
                outputs = []
                for call in action.submit_tool_outputs.tool_calls:
                    if call.function.name == "send_alert":
                        args = json.loads(call.function.arguments)
                        result = send_alert(**args)
                        outputs.append({"tool_call_id": call.id, "output": result})
                run = ai_client.agents.submit_tool_outputs_to_run(
                    thread_id=thread.id, run_id=run.id, tool_outputs=outputs
                )

    messages = ai_client.agents.list_messages(thread_id=thread.id)
    return messages.get_last_message_by_role(MessageRole.ASSISTANT).content[0].text.value
```

---

## Test It

Send a simulated Event Grid event locally:

```python
def test_qa_locally():
    """Test the QA pipeline without a real Event Grid event."""
    pipeline_name = "sales-data-pipeline"
    agent_id = create_qa_agent()

    # Simulate a run with a row count anomaly
    stats = {
        "pipeline_name": pipeline_name,
        "run_id": "test-run-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 45,
        "rows_read": 15000,
        "rows_written": 500,   # Suspiciously low (normally ~14000)
        "null_rates": {"customer_id": 0.0, "amount": 0.35},  # amount spiked!
        "schema_hash": "abc123"
    }

    baseline = {
        "run_count": 30,
        "avg_rows_written": 13800,
        "avg_duration_seconds": 42,
        "schema_hash": "abc123",
        "null_rate_history": {"customer_id": 0.001, "amount": 0.02}
    }

    report = run_qa_analysis(agent_id, pipeline_name, stats, baseline)
    print(report)

test_qa_locally()
```

---

## Common Mistakes

- **Agent not detecting anomalies because baseline is None.** On first run, there's no baseline. Have the agent document that baselines are being established rather than failing silently.
- **Code Interpreter output not included in report.** Always check that `content` blocks include the code output. If the agent generates charts, retrieve them with `get_file_content`.
- **Event Grid event schema varies by ADF version.** Test with `az eventgrid event-subscription show` to confirm the actual fields in your pipeline completion events before coding against them.

---

## Extend It

1. **Great Expectations integration:** Replace the hardcoded thresholds with a Great Expectations suite stored in blob storage. The agent loads and runs expectations as Python code.
2. **Slack digest:** Batch QA results from all pipelines that run overnight. At 8 AM, a timer-triggered function sends a single digest message to Slack with a summary table.
3. **Auto-remediation:** For known failure modes (e.g., null spike in `amount` column always means upstream API was down), the agent doesn't just alert — it calls a remediation function that triggers a pipeline re-run with the backup data source.

---

## Resources

- [Azure Functions Event Grid trigger](https://learn.microsoft.com/azure/azure-functions/functions-bindings-event-grid-trigger)
- [ADF pipeline run events](https://learn.microsoft.com/azure/data-factory/how-to-create-event-trigger)
- [Code Interpreter tool](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/code-interpreter)
- [azure-storage-blob Python SDK](https://learn.microsoft.com/python/api/overview/azure/storage-blob-readme)
