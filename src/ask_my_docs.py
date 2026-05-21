"""
ask_my_docs.py — Ask My Docs: Foundry File Search Agent
Works with azure-ai-projects==2.1.0 + openai==2.37.0

Usage:
  1. Set FOUNDRY_PROJECT_ENDPOINT in .env
  2. Place a PDF at the path in PDF_PATH
  3. Run: python ask_my_docs.py
"""
import os
import pathlib
import time
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
if not PROJECT_ENDPOINT:
    raise ValueError(
        "Set FOUNDRY_PROJECT_ENDPOINT in .env\n"
        "Format: https://<hub>.ai.azure.com/api/projects/<project>"
    )

client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)
openai = client.get_openai_client()


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
            "Answer only using the provided documents. "
            "Always cite the source file and section. "
            "If the answer is not in the documents, say so."
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


def main():
    PDF_PATH = "sample.pdf"   # ← change to your PDF
    STORE_NAME = "ask-my-docs-store"
    MODEL = "gpt-4.1-mini"

    # Step 1: upload
    uploaded = upload_pdf(PDF_PATH)

    # Step 2: create vector store and index
    vs = create_vector_store(uploaded.id, STORE_NAME)

    # Step 3: ask questions
    questions = [
        "What is the main subject of this document?",
        "List any key requirements or commitments mentioned.",
        "Are there any deadlines or dates referenced?",
    ]

    print("\n" + "="*60)
    for q in questions:
        print(f"\n❓ {q}")
        answer, annotations = ask(q, vs.id, MODEL)
        print(f"💬 {answer}")
        for ann in annotations:
            if hasattr(ann, "file_citation"):
                print(f"   ↳ Source: {ann.file_citation.file_id}")

    print("\n" + "="*60)
    print("Done. To reuse this vector store, set VECTOR_STORE_ID=" + vs.id)


if __name__ == "__main__":
    main()
