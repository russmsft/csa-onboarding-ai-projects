# Agent Guide

## Project Overview

This repository is a portfolio of AI projects for Cloud Solution Architects, built on Microsoft Foundry. It combines:

- A master portfolio in `README.md` (the landing page)
- Twelve numbered how-to guides in `docs/how-to/`
- A small Python demo in `src/` for the Ask My Docs RAG pattern

The audience is Cloud Solution Architects with solid cloud experience building hands-on depth in Azure AI and Microsoft Foundry. Contributions should lower the barrier to building and keep every project idea demo-ready.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `README.md` | Landing page and master list of 12 project ideas plus a cross-region failover production-hardening guide, roadmap, service mappings, and per-project guide links |
| `docs/how-to/NN-<name>.md` | Step-by-step build guides matching the numbered project list |
| `src/ask_my_docs.py` | Working Python RAG demo using Azure OpenAI Responses API and File Search |
| `src/cleanup.py` | Cleanup utility for uploaded files and vector stores |
| `.env.example` | Required local environment variables |
| `outputs/` | Generated demo outputs; keep only `.gitkeep` under normal source control |

## Tech Stack

- Python 3.11+
- Azure CLI authentication with `DefaultAzureCredential`
- `openai` Python SDK using the Azure OpenAI endpoint
- `azure-identity` and `python-dotenv`
- Microsoft Foundry / Azure AI Services resources

Keep package versions in `requirements.txt` rather than duplicating them in prose.

## Build and Run

```bash
python -m pip install -r requirements.txt
cp .env.example .env
az login
python src/ask_my_docs.py
python src/cleanup.py
```

`AZURE_OPENAI_ENDPOINT` must point at an Azure AI Services / Azure OpenAI-compatible endpoint. Never commit `.env` or secrets.

## Testing and Validation

There is no formal test suite yet. Before opening a PR:

```bash
python -m compileall src
```

For code changes that touch the live demo, run the affected script against a test Azure AI Services resource and clean up with `python src/cleanup.py`.

## Key Patterns and Conventions

- Use `DefaultAzureCredential` and `get_bearer_token_provider`; do not add API-key based examples.
- Keep the Azure OpenAI API version in one place per script and update related docs when it changes.
- Save generated runtime outputs under `outputs/` using timestamped names.
- Raise clear errors for missing local configuration in runnable scripts.
- Keep how-to guides practical: every guide should have prerequisites, architecture, commands/code, cleanup, and extension ideas.
- Prefer Microsoft Foundry terminology. Avoid presenting standalone Azure OpenAI as the primary platform unless a specific API requires that endpoint shape.

## Adding or Updating a Project Guide

When adding a new guide or renumbering existing guides, update all linked surfaces:

| Change | Also update |
| --- | --- |
| Add or rename `docs/how-to/NN-<name>.md` | `README.md` guide table and learning path |
| Change the project list/order | `README.md`, guide filenames, and README references |
| Change required Azure services | Guide prerequisites, architecture section, and service mapping in the brainstorm |
| Add runnable code | `requirements.txt`, `.env.example`, README setup commands, and CI if validation changes |
| Change output format | `src/ask_my_docs.py`, sample outputs in `outputs/`, and any guide text that describes results |

## Documentation Status

The repository has first-party documentation in `docs/` and a guide index in `README.md`. There is no separate documentation site or deployment pipeline.

## Common Pitfalls

- Do not commit real demo outputs, customer documents, `.env`, or credentials.
- Do not leave uploaded files or vector stores behind after demos; use `src/cleanup.py`.
- Do not introduce portal-only setup steps when a CLI equivalent is available.
- Do not duplicate model/version claims across many files without checking consistency.
