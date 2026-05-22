"""
cleanup.py — List and delete Azure OpenAI vector stores and uploaded files.

Run this after a demo session to avoid ongoing vector storage charges (~$0.10/GB/day).

Usage:
  python src/cleanup.py           # lists all vector stores and files, asks before deleting
  python src/cleanup.py --delete  # deletes ALL vector stores and files (no prompt)

Requires AZURE_OPENAI_ENDPOINT in .env and az login completed.
"""
import argparse
import os
import sys
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

load_dotenv()

ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
if not ENDPOINT:
    print("ERROR: Set AZURE_OPENAI_ENDPOINT in .env")
    sys.exit(1)

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    azure_ad_token_provider=token_provider,
    api_version="2025-04-01-preview",
)


def list_vector_stores():
    try:
        stores = list(client.vector_stores.list())
    except Exception as e:
        print(f"Could not list vector stores: {e}")
        return []
    if not stores:
        print("No vector stores found.")
        return []
    print(f"\n{'ID':<35} {'Name':<30} {'Status':<15} {'Size (bytes)'}")
    print("-" * 90)
    for vs in stores:
        size = getattr(vs, "usage_bytes", "?")
        print(f"{vs.id:<35} {vs.name:<30} {vs.status:<15} {size}")
    return stores


def list_files():
    try:
        files = list(client.files.list(purpose="assistants"))
    except Exception as e:
        print(f"\nCould not list files: {e}")
        return []
    if not files:
        print("\nNo uploaded files found.")
        return []
    print(f"\n{'ID':<40} {'Filename':<35} {'Size (bytes)'}")
    print("-" * 85)
    for f in files:
        print(f"{f.id:<40} {f.filename:<35} {f.bytes}")
    return files


def delete_all(stores, files, force=False):
    if not stores and not files:
        print("\nNothing to delete.")
        return

    if not force:
        confirm = input(
            f"\nDelete {len(stores)} vector store(s) and {len(files)} file(s)? [y/N] "
        ).strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    for vs in stores:
        client.vector_stores.delete(vs.id)
        print(f"  Deleted vector store: {vs.id} ({vs.name})")

    for f in files:
        client.files.delete(f.id)
        print(f"  Deleted file: {f.id} ({f.filename})")

    print("\nCleanup complete.")


def main():
    parser = argparse.ArgumentParser(description="Clean up Azure OpenAI vector stores and files.")
    parser.add_argument("--delete", action="store_true", help="Delete all without prompting")
    args = parser.parse_args()

    print("=== Vector Stores ===")
    stores = list_vector_stores()

    print("\n=== Uploaded Files ===")
    files = list_files()

    if args.delete:
        delete_all(stores, files, force=True)
    else:
        delete_all(stores, files, force=False)


if __name__ == "__main__":
    main()
