# Copilot Instructions

This is a portfolio of AI projects for Microsoft Cloud Solution Architects — 12 AI project ideas with step-by-step how-to guides to build AI skills, demo capabilities to customers, and kick-start co-build POCs. All projects use **Microsoft Foundry** as the AI platform (not standalone Azure OpenAI resources).

## Repository Structure

- `README.md` — Landing page and master list of all 12 project ideas with ratings, service mappings, phased roadmap, and per-project links to how-to guides
- `docs/how-to/NN-<name>.md` — Step-by-step build guides (numbered 01–12, matching the brainstorm order; 13 is a cross-region failover capstone)
- `src/` — Working Python scripts (currently `ask_my_docs.py` and `cleanup.py`)
- `outputs/` — Generated results from script runs (timestamped `.md` and `.json` files)
- `.env.example` — Template for required environment variables

## Running the Code

```bash
# Install dependencies
pip install "openai>=1.30.0" azure-identity python-dotenv

# Set up environment
cp .env.example .env
# Edit .env with your AZURE_OPENAI_ENDPOINT

# Authenticate
az login

# Run the Ask My Docs RAG demo
python src/ask_my_docs.py

# Clean up vector stores and files after demos
python src/cleanup.py          # interactive — lists then asks
python src/cleanup.py --delete # force delete all
```

## Code Conventions

- **Authentication:** Always use `DefaultAzureCredential` with `get_bearer_token_provider` — never API keys. Required RBAC role is `Cognitive Services OpenAI Contributor`.
- **API version:** Use `2025-04-01-preview` for Azure OpenAI client initialization.
- **Output:** Scripts save results to `outputs/` with `results_<timestamp>.md` and `.json` formats.
- **Config:** Environment variables via `.env` + `python-dotenv`. Only `AZURE_OPENAI_ENDPOINT` is currently required.
- **Dependencies:** Keep Python dependencies in `requirements.txt`; do not duplicate package lists across scripts and docs unless the guide needs a copy/paste quickstart.

## How-To Guide Format

Each guide in `docs/how-to/` follows this structure:
1. Opening hook — one-sentence pitch for what the project does
2. **What You're Building** — concrete description of the end result
3. **Business Value** — who/why/outcome table
4. **Prerequisites** — Azure resources, CLI commands, RBAC roles, pip installs
5. **Architecture** — ASCII or Mermaid diagram of the flow
6. Step-by-step build sections with complete code blocks
7. **Extend It** — ideas for taking the project further

## Writing Style

- Write for CSAs with strong cloud backgrounds building depth in Azure AI — explain AI concepts, skip Azure basics.
- Every guide should produce something demo-ready — not just theory.
- Include full CLI commands for Azure resource setup (don't assume portal-only).
- Call out cost implications and cleanup steps for demo resources.
- Use Microsoft Foundry terminology (not "Azure AI Studio" or "Azure OpenAI" as standalone).

## Test Conventions

There is no formal test suite yet. For code changes, run:

```bash
python -m compileall src
```

For changes that touch live Azure AI / Foundry behavior, manually validate against a test resource and run `python src/cleanup.py` afterward to remove uploaded files and vector stores.

## Maintenance Matrix

| If you change | Also update |
| --- | --- |
| `src/ask_my_docs.py` runtime behavior, model, API version, output format, or required roles | `docs/how-to/01-ask-my-docs.md`, `README.md`, `.env.example`, `requirements.txt`, and sample output expectations |
| `src/cleanup.py` cleanup behavior or CLI flags | `README.md`, `docs/how-to/01-ask-my-docs.md`, and PR checklist language if validation cleanup changes |
| Python dependencies | `requirements.txt`, README setup commands, relevant guide prerequisites, and `.github/workflows/*.yml` if install or validation changes |
| Required environment variables | `.env.example`, README setup steps, and affected how-to prerequisites |
| `README.md` project ordering, names, difficulty, model choices, or roadmap | matching `docs/how-to/NN-<name>.md` files |
| A `docs/how-to/NN-<name>.md` filename, title, or project scope | README at-a-glance table, per-project section, and roadmap links |
| Azure service choices, RBAC roles, or CLI setup commands in a guide | The guide prerequisites, architecture section, cleanup notes, and the matching project section in `README.md` |
| Generated output examples in `outputs/` | Keep committed examples non-confidential and update docs that describe the output shape |
