# 09 — Competitive Intelligence Dashboard: Weekly Competitor Monitoring on Autopilot

Schedule an agent to search for competitor news, generate trend charts, and store results in Cosmos DB — then surface everything in a dashboard that refreshes automatically.

---

## What You're Building

An Azure Functions timer trigger that runs every Monday morning. It fires a Foundry agent with `WebSearchTool` grounding (Bing) to pull competitor news and product updates, then hands the results to Code Interpreter to generate trend charts. Results land in Cosmos DB. An Azure Static Web App reads from Cosmos DB via a lightweight API and renders the dashboard.

---

## Prerequisites

- Microsoft Foundry project with GPT-4.1 deployed + Bing grounding enabled
- Azure Cosmos DB account (Serverless tier works well for low-frequency writes)
- Azure Static Web Apps resource
- Python 3.11+, `azure-functions`, `azure-ai-projects`, `azure-cosmos`

```bash
pip install azure-ai-projects azure-identity azure-functions \
  azure-cosmos python-dotenv
```

---

## Architecture

![Competitive Intelligence architecture: Functions timer → Foundry Agent GPT-4.1 with Web Search and Code Interpreter → Cosmos DB → Functions HTTP API → Azure Static Web App dashboard](images/09-competitive-intelligence-dashboard-architecture.png)

---

## Step-by-Step Build

### Step 1 — Create Cosmos DB

```bash
COSMOS_ACCOUNT="competitive-intel-db"
DB_NAME="competitor-intel"
CONTAINER_NAME="weekly-intel"

az cosmosdb create \
  --name $COSMOS_ACCOUNT \
  --resource-group $RG \
  --locations regionName=eastus2 \
  --capabilities EnableServerless

az cosmosdb sql database create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RG \
  --name $DB_NAME

az cosmosdb sql container create \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RG \
  --database-name $DB_NAME \
  --name $CONTAINER_NAME \
  --partition-key-path "/competitor"
```

### Step 2 — Enable Bing grounding in Foundry

1. In the [AI Foundry portal](https://ai.azure.com), navigate to your project
2. Go to **Settings** → **Connections** → **Add connection**
3. Select **Bing Search** and authorize
4. Note the connection name — you'll reference it in `WebSearchTool`

### Step 3 — Create the intelligence agent

```python
import os
import json
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient
from azure.ai.projects.models import (
    WebSearchTool,
    CodeInterpreterTool,
    PromptAgentDefinition,
    MessageRole
)

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
BING_CONNECTION_NAME = os.environ["BING_CONNECTION_NAME"]
COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
DB_NAME = "competitor-intel"
CONTAINER_NAME = "weekly-intel"

credential = DefaultAzureCredential()
ai_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)
cosmos = CosmosClient(url=COSMOS_ENDPOINT, credential=credential)
container = cosmos.get_database_client(DB_NAME).get_container_client(CONTAINER_NAME)


def create_intel_agent() -> str:
    web_search = WebSearchTool(connection_name=BING_CONNECTION_NAME)
    code_interpreter = CodeInterpreterTool()

    agent_def = PromptAgentDefinition(
        model="gpt-4.1",
        name="competitive-intel-agent",
        instructions="""You are a competitive intelligence analyst. Your job each week:

1. Search for recent news (last 7 days) about each competitor provided
2. Categorize findings: product launches, pricing changes, partnerships, executive moves, negative press
3. Write a brief analysis (2-3 sentences) for each competitor
4. Use Code Interpreter to generate a sentiment trend bar chart (matplotlib) showing:
   - X-axis: competitor names
   - Y-axis: news sentiment score (-5 to +5)
   - Title: "Competitor News Sentiment — Week of [date]"
5. Save the chart as a PNG file

Format your text output as JSON with this structure:
{
  "week_of": "YYYY-MM-DD",
  "competitors": [
    {
      "name": "CompetitorName",
      "sentiment_score": <-5 to 5>,
      "key_developments": ["...", "..."],
      "analysis": "...",
      "sources": ["url1", "url2"]
    }
  ],
  "overall_summary": "..."
}

Be factual. Cite sources. Don't speculate.""",
        tools=[*web_search.definitions, *code_interpreter.definitions],
        tool_resources=code_interpreter.resources,
    )
    agent = ai_client.agents.create_version(definition=agent_def)
    return agent.id
```

### Step 4 — Run the weekly intelligence sweep

```python
def run_weekly_intel(agent_id: str, competitors: list[str]) -> dict:
    """Run competitive intelligence sweep for the given competitor list."""
    week_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    competitor_list = ", ".join(competitors)

    thread = ai_client.agents.create_thread()
    ai_client.agents.create_message(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=(
            f"Run a competitive intelligence sweep for week of {week_str}.\n"
            f"Competitors to analyze: {competitor_list}\n\n"
            "Search for news from the last 7 days for each. "
            "Generate the sentiment chart and return structured JSON."
        )
    )

    print(f"Running intel sweep for: {competitor_list}")
    run = ai_client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent_id
    )

    if run.status != "completed":
        raise RuntimeError(f"Intel run failed: {run.status}\n{run.last_error}")

    messages = ai_client.agents.list_messages(thread_id=thread.id)
    last = messages.get_last_message_by_role(MessageRole.ASSISTANT)

    # Extract text and file outputs
    intel_text = ""
    chart_file_id = None

    for block in last.content:
        if hasattr(block, "text"):
            intel_text += block.text.value
        elif hasattr(block, "image_file"):
            chart_file_id = block.image_file.file_id

    # Parse JSON from the response
    intel_data = {}
    try:
        # Find JSON block in the response
        import re
        json_match = re.search(r'\{[\s\S]*\}', intel_text)
        if json_match:
            intel_data = json.loads(json_match.group())
    except json.JSONDecodeError:
        intel_data = {"raw": intel_text, "week_of": week_str}

    # Download chart if generated
    chart_b64 = None
    if chart_file_id:
        chart_bytes = b"".join(ai_client.agents.get_file_content(chart_file_id))
        chart_b64 = base64.b64encode(chart_bytes).decode()

    return {**intel_data, "chart_b64": chart_b64, "thread_id": thread.id}
```

### Step 5 — Store results in Cosmos DB

```python
def store_intel_results(intel_data: dict, competitors: list[str]):
    """Write one document per competitor per week to Cosmos DB."""
    week_of = intel_data.get("week_of", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    # Store aggregate document
    aggregate_doc = {
        "id": f"weekly-{week_of}",
        "competitor": "_aggregate",
        "week_of": week_of,
        "overall_summary": intel_data.get("overall_summary", ""),
        "chart_b64": intel_data.get("chart_b64"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "competitor_count": len(competitors)
    }
    container.upsert_item(aggregate_doc)

    # Store per-competitor documents
    for comp_data in intel_data.get("competitors", []):
        name = comp_data.get("name", "unknown")
        doc = {
            "id": f"{name.lower().replace(' ', '-')}-{week_of}",
            "competitor": name,
            "week_of": week_of,
            **comp_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        container.upsert_item(doc)
        print(f"Stored intel for: {name}")
```

### Step 6 — Azure Function timer trigger

```python
# function_app.py
import azure.functions as func
import logging
import json

app = func.FunctionApp()
logger = logging.getLogger(__name__)

COMPETITORS = [
    "Competitor A",
    "Competitor B",
    "Competitor C"
]


@app.timer_trigger(
    arg_name="timer",
    schedule="0 0 7 * * MON"   # Every Monday at 07:00 UTC
)
def weekly_intel_sweep(timer: func.TimerRequest):
    if timer.past_due:
        logger.warning("Timer is past due — running catch-up sweep")

    logger.info("Starting weekly competitive intelligence sweep")

    agent_id = os.environ.get("INTEL_AGENT_ID") or create_intel_agent()
    intel_data = run_weekly_intel(agent_id, COMPETITORS)
    store_intel_results(intel_data, COMPETITORS)

    logger.info(f"Sweep complete. Analyzed {len(COMPETITORS)} competitors.")


@app.route(route="intelligence", methods=["GET"])
def get_intelligence(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP endpoint for the dashboard to fetch stored results."""
    weeks = int(req.params.get("weeks", "8"))
    competitor = req.params.get("competitor")

    query = "SELECT * FROM c ORDER BY c.week_of DESC OFFSET 0 LIMIT @limit"
    params = [{"name": "@limit", "value": weeks * (len(COMPETITORS) + 1)}]

    if competitor:
        query = ("SELECT * FROM c WHERE c.competitor = @comp "
                 "ORDER BY c.week_of DESC OFFSET 0 LIMIT @limit")
        params.append({"name": "@comp", "value": competitor})

    results = list(container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True
    ))

    return func.HttpResponse(
        json.dumps(results),
        status_code=200,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )
```

---

## Test It

Run the sweep manually without waiting for Monday:

```bash
# Trigger the function locally
func start

# In another terminal:
curl -X POST http://localhost:7071/admin/functions/weekly_intel_sweep \
  -H "Content-Type: application/json" \
  -d '{}'

# Check the results API
curl "http://localhost:7071/api/intelligence?weeks=4"
```

Verify in Cosmos DB:

```bash
az cosmosdb sql query \
  --account-name $COSMOS_ACCOUNT \
  --resource-group $RG \
  --database-name competitor-intel \
  --container-name weekly-intel \
  --query-text "SELECT c.competitor, c.week_of, c.sentiment_score FROM c" \
  --output table
```

---

## Common Mistakes

- **Bing search returning stale results.** Web Search grounding uses recency ranking but doesn't guarantee freshness. Add `"in the last 7 days"` to your search queries explicitly.
- **Cosmos DB partition key strategy.** Using `competitor` as partition key is fine for reads by competitor. If you query by `week_of` frequently, use a composite index or add a synthetic partition key.
- **Chart not generated.** Code Interpreter needs matplotlib installed in its sandbox — it comes pre-installed. If charts aren't appearing, check that your agent instructions explicitly say "save as PNG file attachment."

---

## Extend It

1. **Email digest:** Add a step after Cosmos DB write that calls SendGrid API to email the weekly dashboard summary to stakeholders — no login required.
2. **Historical trend lines:** Store 12 weeks of sentiment scores per competitor, then have Code Interpreter generate line charts showing sentiment trends over time.
3. **Slack alerts on negative spikes:** Add a threshold check — if any competitor's sentiment_score drops below -3, immediately post to a Slack channel with the key developments.

---

## Resources

- [WebSearchTool (Bing grounding)](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/bing-grounding)
- [Azure Cosmos DB Python SDK](https://learn.microsoft.com/python/api/overview/azure/cosmos-readme)
- [Azure Functions timer trigger](https://learn.microsoft.com/azure/azure-functions/functions-bindings-timer)
- [Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps/overview)
