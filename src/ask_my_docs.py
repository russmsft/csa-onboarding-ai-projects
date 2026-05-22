explorer "C:\Users\rubradfo\vbd-copilot\csa-onboarding-ai-projects\outputs"
"""
ask_my_docs.py — Ask My Docs: RAG over documents using Azure OpenAI
Works with openai>=1.30.0

Usage:
  1. Set AZURE_OPENAI_ENDPOINT in .env  (e.g. https://<name>.cognitiveservices.azure.com/)
  2. Place a PDF at the path in PDF_PATH
  3. Run: python ask_my_docs.py

Authentication: uses DefaultAzureCredential (az login / managed identity).
Required role: Cognitive Services OpenAI Contributor (not Cognitive Services User)
Results are saved to outputs/results_<timestamp>.md automatically.
"""
import json
import os
import pathlib
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

load_dotenv()

ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
if not ENDPOINT:
    raise ValueError(
        "Set AZURE_OPENAI_ENDPOINT in .env\n"
        "Format: https://<account-name>.cognitiveservices.azure.com/"
    )

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

openai = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2025-04-01-preview",
)


def upload_pdf(pdf_path: str):
    """Upload a PDF to Foundry file storage and return the file object."""
    path = pathlib.Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    print(f"Uploading {path.name} ({path.stat().st_size // 1024} KB)...")
    with open(path, "rb") as f:
        uploaded = openai.files.create(file=f, purpose="assistants")
    print(f"  File ID: {uploaded.id}  status={uploaded.status}")
    return uploaded


def create_vector_store(file_id: str, store_name: str):
    """Create a vector store, attach the file, and wait for indexing."""
    print(f"Creating vector store '{store_name}'...")
    vs = openai.vector_stores.create(name=store_name, file_ids=[file_id])
    print(f"  Vector store ID: {vs.id}  status={vs.status}")

    # Poll until indexing is complete
    for _ in range(30):
        if vs.status == "completed":
            break
        time.sleep(3)
        vs = openai.vector_stores.retrieve(vs.id)
        print(f"  Waiting for indexing... status={vs.status}")
    else:
        raise TimeoutError("Vector store indexing did not complete within 90 seconds.")

    print(f"  Indexing complete. Chunks indexed: {vs.file_counts.completed}")
    return vs


_file_name_cache: dict[str, str] = {}


def resolve_filename(file_id: str) -> str:
    """Resolve a file ID to its original filename, with caching."""
    if file_id not in _file_name_cache:
        try:
            _file_name_cache[file_id] = openai.files.retrieve(file_id).filename
        except Exception:
            _file_name_cache[file_id] = file_id
    return _file_name_cache[file_id]


def ask(question: str, vector_store_id: str, model: str = "gpt-4.1-mini") -> str:
    """Ask a question grounded in the vector store using Responses API."""
    response = openai.responses.create(
        model=model,
        input=question,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store_id],
        }],
        instructions=(
            "You MUST NOT answer from general knowledge. "
            "Only answer using information retrieved from the provided documents. "
            "If the answer cannot be found in the retrieved document chunks, respond with exactly: "
            "'I cannot find that information in the provided documents.' "
            "Do not guess, infer, or supplement from training data."
        ),
        include=["file_search_call.results"],
    )

    # Extract answer text
    answer = ""
    for item in response.output:
        if hasattr(item, "type") and item.type == "message":
            for block in item.content:
                if hasattr(block, "text"):
                    answer = block.text
                    break

    # Print citations if present
    annotations = []
    for item in response.output:
        if hasattr(item, "type") and item.type == "message":
            for block in item.content:
                if hasattr(block, "annotations"):
                    annotations.extend(block.annotations)

    return answer, annotations


def save_results(doc_name: str, vector_store_id: str, results: list[dict], output_dir: pathlib.Path):
    """Save Q&A results to a markdown file and a JSON file in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = f"results_{timestamp}"

    # Markdown report
    md_path = output_dir / f"{stem}.md"
    lines = [
        f"# Ask My Docs — Results",
        f"",
        f"**Document:** {doc_name}  ",
        f"**Vector store:** `{vector_store_id}`  ",
        f"**Run at:** {datetime.now(timezone.utc).isoformat()}",
        f"",
        "---",
        "",
    ]
    for r in results:
        lines.append(f"### ❓ {r['question']}")
        lines.append(f"")
        lines.append(f"{r['answer']}")
        lines.append(f"")
        for src in r.get("sources", []):
            lines.append(f"*↳ Source: `{src}`*  ")
        lines.append("")
        lines.append("---")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # JSON for programmatic use
    json_path = output_dir / f"{stem}.json"
    json_path.write_text(
        json.dumps({"document": doc_name, "vector_store_id": vector_store_id, "results": results}, indent=2),
        encoding="utf-8",
    )

    print(f"\n📄 Results saved:")
    print(f"   Markdown: {md_path}")
    print(f"   JSON:     {json_path}")
    return md_path, json_path


def main():
    # Resolve sample.txt relative to the repo root (one level above src/)
    _REPO_ROOT = pathlib.Path(__file__).parent.parent
    PDF_PATH = str(_REPO_ROOT / "sample.txt")   # ← change to your PDF or .txt document
    STORE_NAME = "ask-my-docs-store"
    MODEL = "gpt-4.1-mini"
    OUTPUT_DIR = _REPO_ROOT / "outputs"

    # Step 1: upload
    uploaded = upload_pdf(PDF_PATH)

    # Step 2: create vector store and index
    vs = create_vector_store(uploaded.id, STORE_NAME)

    # Step 3: ask questions
    questions = [
        "What is the main subject of this document?",
        "List any key requirements or commitments mentioned.",
        "Are there any deadlines or dates referenced?",
    ]    cd C:\Users\rubradfo\vbd-copilot\csa-onboarding-ai-projects
    
    # See what's there (safe — no deletions yet)
    python src\cleanup.py
    
    # Then type y/n when it asks if you want to delete

    print("\n" + "="*60)
    results = []
    for q in questions:
        print(f"\n❓ {q}")
        answer, annotations = ask(q, vs.id, MODEL)
        print(f"💬 {answer}")
        sources = []
        for ann in annotations:
            if hasattr(ann, "file_citation"):
                filename = resolve_filename(ann.file_citation.file_id)
                print(f"   ↳ Source: {filename}")
                sources.append(filename)
        results.append({"question": q, "answer": answer, "sources": sources})

    print("\n" + "="*60)
    print("Done. To reuse this vector store, set VECTOR_STORE_ID=" + vs.id)

    # Step 4: save results
    save_results(
        doc_name=pathlib.Path(PDF_PATH).name,
        vector_store_id=vs.id,
        results=results,
        output_dir=OUTPUT_DIR,
    )


if __name__ == "__main__":
    main()
