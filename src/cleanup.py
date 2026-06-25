"""
cleanup.py — List and delete Azure OpenAI vector stores and uploaded files.

Run this after a demo session to avoid ongoing vector storage charges (~$0.10/GB/day).

By default this only targets resources created by this project: vector stores
whose name starts with --prefix (default "ask-my-docs") and the files attached
to them. Pass --all to target every vector store and file on the endpoint —
use with care, as the endpoint may be shared with other projects or people.

Usage:
  python src/cleanup.py                    # list project stores/files, ask before deleting
  python src/cleanup.py --delete           # delete project stores/files (no prompt)
  python src/cleanup.py --prefix my-store  # use a different name prefix
  python src/cleanup.py --all --delete     # delete ALL stores/files on the endpoint

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


def list_vector_stores(prefix=None):
    try:
        stores = list(client.vector_stores.list())
    except Exception as e:
        print(f"Could not list vector stores: {e}")
        return []
    if prefix:
        stores = [vs for vs in stores if (vs.name or "").startswith(prefix)]
    if not stores:
        print("No vector stores found.")
        return []
    print(f"\n{'ID':<35} {'Name':<30} {'Status':<15} {'Size (bytes)'}")
    print("-" * 90)
    for vs in stores:
        size = getattr(vs, "usage_bytes", "?")
        print(f"{vs.id:<35} {vs.name:<30} {vs.status:<15} {size}")
    return stores


def files_attached_to(stores):
    """Return the set of file IDs attached to the given vector stores."""
    file_ids = set()
    for vs in stores:
        try:
            for vsf in client.vector_stores.files.list(vs.id):
                file_ids.add(vsf.id)
        except Exception as e:
            print(f"  Could not list files for vector store {vs.id}: {e}")
    return file_ids


def list_files(only_ids=None):
    try:
        files = list(client.files.list(purpose="assistants"))
    except Exception as e:
        print(f"\nCould not list files: {e}")
        return []
    if only_ids is not None:
        files = [f for f in files if f.id in only_ids]
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
    parser.add_argument("--delete", action="store_true", help="Delete without prompting")
    parser.add_argument(
        "--prefix",
        default="ask-my-docs",
        help="Only target vector stores whose name starts with this prefix (default: ask-my-docs)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Target ALL vector stores and files on the endpoint, ignoring --prefix",
    )
    args = parser.parse_args()

    prefix = None if args.all else args.prefix
    scope = "ALL stores/files on the endpoint" if args.all else f"stores named '{prefix}*'"
    print(f"=== Vector Stores ({scope}) ===")
    stores = list_vector_stores(prefix=prefix)

    print("\n=== Uploaded Files ===")
    if args.all:
        files = list_files()
    else:
        # Only files attached to the matched stores are in scope
        files = list_files(only_ids=files_attached_to(stores))

    delete_all(stores, files, force=args.delete)


if __name__ == "__main__":
    main()
