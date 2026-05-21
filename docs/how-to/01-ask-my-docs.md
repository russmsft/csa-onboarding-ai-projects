# 01 — Ask My Docs: Build a Foundry File Search Agent

Give your documents a voice. This guide wires up a Foundry prompt agent with File Search so you can upload PDFs and get cited, accurate answers back in seconds.

---

## What You're Building

A Python script that uploads a PDF to Microsoft Foundry, creates a vector store over it, and attaches a `FileSearchTool` to a GPT-4.1-mini agent. You ask questions in plain English; the agent returns answers with document citations so you can verify every claim.

This is the fastest path to production RAG — no custom chunking pipeline, no vector DB to manage, no embeddings code to write yourself.

---

## Prerequisites

- Azure subscription with Microsoft Foundry (AI Foundry hub + project created at [https://ai.azure.com](https://ai.azure.com))
- Python 3.11+
- `azure-ai-projects >= 2.1.0`, `openai >= 2.37.0`, and `azure-identity` installed
- Azure CLI logged in (`az login`) with Contributor on the Foundry project
- A PDF you want to query (a product spec, runbook, or HR policy works fine)

```bash
pip install "azure-ai-projects>=2.1.0" azure-identity python-dotenv
```

> **Note on SDK versions:** As of May 2026, `azure-ai-projects` 2.x uses the OpenAI client (`get_openai_client()`) for all file, vector store, and agent interactions. The older `client.agents.*` sub-client from v1.x is no longer available. The code in this guide targets v2.1.0+.

---

## Architecture

```
You (Python script)
        │
        ▼
AIProjectClient ──► Foundry Agent Service
        │                    │
        │            FileSearchTool
        │                    │
        │            Vector Store (Foundry-managed)
        │                    │
        │            Uploaded PDF(s)
        │
        ▼
  Agent Thread ──► GPT-4.1-mini ──► Response + Citations
```

**Data flow:** Your PDF is uploaded to Foundry storage → chunked and embedded automatically → stored in a managed vector store → retrieved at query time → passed as context to GPT-4.1-mini → response includes `[source: filename, page N]` citations.

---

## Step-by-Step Build

### Step 1 — Set your project endpoint

```bash
# Find your endpoint in AI Foundry portal: Project → Overview → "API endpoint"
# It looks like: https://<hub-name>.ai.azure.com/api/projects/<project-name>
export FOUNDRY_PROJECT_ENDPOINT="https://<hub>.ai.azure.com/api/projects/<project>"
```

Store it in a `.env` file — never hardcode it.

### Step 2 — Install dependencies

```bash
pip install "azure-ai-projects>=2.1.0" azure-identity python-dotenv
```

### Step 3 — Create the client

```python
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]

# AIProjectClient authenticates with your az login token
client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)

# All file, vector store, and agent calls go through the OpenAI client
openai = client.get_openai_client()
```

`DefaultAzureCredential` picks up your `az login` token automatically. No API keys needed.

### Step 4 — Upload your document and create a vector store

```python
import pathlib
import time

def upload_pdf(pdf_path: str):
    """Upload a PDF to Foundry and return the file object."""
    path = pathlib.Path(pdf_path)
    print(f"Uploading {path.name} ({path.stat().st_size // 1024} KB)...")
    with open(path, "rb") as f:
        uploaded = openai.files.create(file=f, purpose="assistants")
    print(f"  File ID: {uploaded.id}  status={uploaded.status}")
    return uploaded

def create_vector_store(file_id: str, store_name: str):
    """Create a vector store, attach the file, and poll until indexed."""
    print(f"Creating vector store '{store_name}'...")
    vs = openai.vector_stores.create(name=store_name, file_ids=[file_id])
    print(f"  Vector store ID: {vs.id}  status={vs.status}")

    for _ in range(30):
        if vs.status == "completed":
            break
        time.sleep(3)
        vs = openai.vector_stores.retrieve(vs.id)
        print(f"  Waiting for indexing... status={vs.status}")
    else:
        raise TimeoutError("Vector store indexing did not complete within 90 seconds.")

    print(f"  Indexing complete. Chunks: {vs.file_counts.completed}")
    return vs
```

> **Gotcha:** For large PDFs (>50 MB) indexing can take a couple of minutes. The polling loop above retries for up to 90 seconds; increase `range(30)` and `time.sleep(3)` for larger files.

### Step 5 — Ask a question using the Responses API

In SDK v2.1.0, you pass the `file_search` tool directly to `openai.responses.create()`. No separate agent registration needed for basic Q&A.

```python
def ask(question: str, vector_store_id: str, model: str = "gpt-4.1-mini"):
    """Ask a question grounded in the vector store."""
    response = openai.responses.create(
        model=model,
        input=question,
        instructions=(
            "Answer only using the provided documents. "
            "Always cite the source file and section. "
            "If the answer is not in the documents, say so — do not guess."
        ),
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store_id],
        }],
        include=["file_search_call.results"],
    )

    # Extract answer text and citations from output items
    answer = ""
    annotations = []
    for item in response.output:
        if hasattr(item, "type") and item.type == "message":
            for block in item.content:
                if hasattr(block, "text"):
                    answer = block.text
                if hasattr(block, "annotations"):
                    annotations.extend(block.annotations)

    print(f"💬 {answer}")
    for ann in annotations:
        if hasattr(ann, "file_citation"):
            print(f"   ↳ Source: {ann.file_citation.file_id}")
    return answer
```

> **Model note:** GPT-4.1-mini is the right pick here — fast and cheap for Q&A. Switch to GPT-4.1 if you need deeper reasoning over complex technical docs.

### Step 6 — Wire it all together

```python
def main():
    PDF_PATH = "your-document.pdf"    # ← change to your PDF
    STORE_NAME = "ask-my-docs-store"

    uploaded = upload_pdf(PDF_PATH)
    vs = create_vector_store(uploaded.id, STORE_NAME)

    questions = [
        "What is the main subject of this document?",
        "List any key requirements or commitments mentioned.",
        "Are there any deadlines or dates referenced?",
    ]

    print("\n" + "="*60)
    for q in questions:
        print(f"\n❓ {q}")
        ask(q, vs.id)

    print(f"\nTo reuse: VECTOR_STORE_ID={vs.id}")

if __name__ == "__main__":
    main()
```

The complete, runnable version of this script is at `src/ask_my_docs.py` in this repo.

---

## Test It

Run the script against a PDF you know well so you can verify accuracy:

```bash
# Copy .env.example → .env and set your endpoint
cp .env.example .env
# Edit .env with your FOUNDRY_PROJECT_ENDPOINT

python src/ask_my_docs.py
```

Expected output:

```
Uploading my-policy.pdf (142 KB)...
  File ID: file-abc123  status=processed
Creating vector store 'ask-my-docs-store'...
  Vector store ID: vs-xyz789  status=in_progress
  Waiting for indexing... status=in_progress
  Indexing complete. Chunks: 1

============================================================

❓ What is the main subject of this document?
💬 The document covers the company's remote work policy, including eligibility
criteria, equipment provisions, and security requirements for employees working
outside the office.
   ↳ Source: file-abc123

❓ List any key requirements or commitments mentioned.
💬 Key requirements include: VPN usage for all remote sessions, encrypted
laptop storage, and manager approval for remote work schedules exceeding
3 days per week.
   ↳ Source: file-abc123
```

**Verify citations are accurate:** Open the PDF and confirm the cited content actually says what the agent claims. If citations are wrong or missing, check that the PDF isn't a scanned image — Document Intelligence preprocessing (Guide 05) may be needed.

**Add a second document:**

```python
with open("second-doc.pdf", "rb") as f:
    uploaded2 = openai.files.create(file=f, purpose="assistants")

# Add to existing vector store
openai.vector_stores.files.create(
    vector_store_id=vs.id,
    file_id=uploaded2.id
)
```

---

## Common Mistakes

- **Scanned PDFs return empty text.** Foundry's file upload does basic text extraction. If your PDF is a scanned image, pre-process it with Azure AI Document Intelligence first (see Guide 05).
- **Agent answers questions not in the docs.** Check your system prompt — add `"Only answer using the provided documents."` if hallucination is a problem.
- **Thread reuse leaks context.** Create a new thread for each user session. Reusing threads across users exposes previous conversation history.

---

## Extend It

1. **Multi-tenant isolation:** Create a separate vector store per user/team. Pass the correct `vector_store_id` based on the authenticated user's group membership from Entra ID.
2. **Streaming responses:** Replace `create_and_process_run` with `create_stream` and yield tokens to a frontend for real-time display.
3. **Slack / Teams bot:** Wrap the `ask()` function in an Azure Function with an HTTP trigger, then register it as a Teams bot via Bot Framework. Now your whole org can query the docs from Teams.

---

## Resources

- [Foundry Agent Service — File Search](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/file-search)
- [azure-ai-projects SDK reference](https://learn.microsoft.com/python/api/overview/azure/ai-projects-readme)
- [Vector stores in Foundry](https://learn.microsoft.com/azure/ai-foundry/agents/concepts/vector-stores)
- [DefaultAzureCredential auth chain](https://learn.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)
