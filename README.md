# CSA Onboarding AI Projects

[![AI Ready](https://img.shields.io/badge/AI--Ready-yes-brightgreen?style=flat)](https://github.com/johnpapa/ai-ready)

A curated portfolio of AI project ideas for new Cloud Solution Architects at Microsoft CSU Cloud & AI. Built on Microsoft Foundry.

## What's in Here

| File | Description |
|------|-------------|
| `docs/ai-brainstorming.md` | 12 AI project ideas with impact/difficulty ratings, Azure service mappings, phased roadmap, and model selection cheat sheet |

## Who This Is For

New CSAs with solid cloud/dev backgrounds who are new to Azure AI and Microsoft Foundry. The ideas serve two purposes:

- **Demo assets** — personal projects you build once and bring into every customer meeting
- **Co-build templates** — POC starters you adapt to a customer's data and deploy alongside them

## Quick Start

Start with these three ideas from the brainstorm (in order):

1. **Ask My Docs** — RAG in a day using Foundry Agent Service + File Search
2. **Meeting Minutes Agent** — Audio transcription + structured extraction
3. **Internal Policy Chatbot** — Foundry IQ (turnkey RAG, no pipeline to build)

These three give you working Foundry experience and customer-ready demos within your first two weeks.

## Prerequisites

- Azure subscription with Microsoft Foundry access
- Azure CLI (`az`) installed and logged in
- Python 3.11+ or .NET 8+ depending on the idea you're building
- VS Code with the Foundry extension (optional but recommended)

## Environment Setup

```bash
# Install Azure CLI
winget install Microsoft.AzureCLI

# Log in
az login

# Create a Foundry resource and project via portal:
# https://ai.azure.com

# Install the Python dependencies used by the sample scripts
pip install -r requirements.txt
```

## How to Use the Brainstorm

Open `docs/ai-brainstorming.md` and follow the phased roadmap:

- **Phase 1 (0-3 months):** Ideas 1, 2, 4, 3, 6 — build your foundation
- **Phase 2 (3-9 months):** Pick from Ideas 5, 7, 8, 9 based on your customer mix
- **Phase 3 (9-18 months):** Ideas 10, 11, 12 — lead complex engagements

## Key Resources

- [Microsoft Foundry portal](https://ai.azure.com)
- [Foundry Agent Service overview](https://learn.microsoft.com/azure/ai-foundry/agents/overview)
- [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/overview/agent-framework-overview)
- [Foundry Models catalog](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure)
- [Baseline reference architecture](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat)

## Contributing

Fork the repo, create a branch, and open a pull request with a short summary and validation notes. For Python changes, install dependencies with `pip install -r requirements.txt` and run:

```bash
python -m compileall src
```

If you update a how-to guide, also check the guide table and learning path in this README plus the master list in `docs/ai-brainstorming.md`.

## Notes

- All ideas use **Microsoft Foundry** as the AI platform — not standalone Azure OpenAI resources
- Model recommendations are current as of May 2026; check the Foundry catalog for the latest
- The `.gitignore` excludes this folder from the main repo — generated artifacts stay local


## How-To Guides

Step-by-step build guides for each project idea. Written for CSAs with solid cloud backgrounds who are new to Azure AI and Microsoft Foundry. Every guide includes real Python code, CLI commands, architecture diagrams, and "extend it" ideas.

| Guide | Description | Key Services |
|-------|-------------|--------------|
| [01 — Ask My Docs](docs/how-to/01-ask-my-docs.md) | RAG agent with File Search — upload PDFs, get cited answers | Foundry Agent Service, GPT-4.1-mini, FileSearchTool |
| [02 — Meeting Minutes Agent](docs/how-to/02-meeting-minutes-agent.md) | Transcribe audio + extract structured action items | Whisper, GPT-4.1-mini, JSON Schema |
| [03 — Email Triage Agent](docs/how-to/03-email-triage-agent.md) | Classify, draft, and route incoming email via Service Bus | GPT-4.1-mini, GPT-5.4-mini, FunctionTool, Service Bus |
| [04 — Policy Chatbot](docs/how-to/04-policy-chatbot.md) | Foundry IQ-grounded HR/IT chatbot on App Service with Entra auth | Foundry IQ, GPT-4.1-mini, App Service, Entra ID |
| [05 — Contract Clause Analyzer](docs/how-to/05-contract-clause-analyzer.md) | Risk-score a contract PDF using 1M context + Code Interpreter | Document Intelligence, GPT-5.4, CodeInterpreterTool |
| [06 — Multi-Agent Incident Responder](docs/how-to/06-multi-agent-incident-responder.md) | Concurrent fan-out agents: diagnose + research + communicate | GPT-4.1, App Insights, AI Search, FunctionTool |
| [07 — Data Pipeline QA Agent](docs/how-to/07-data-pipeline-qa-agent.md) | Anomaly detection on pipeline run stats via Event Grid trigger | GPT-4.1-mini, CodeInterpreterTool, Event Grid, Azure Functions |
| [08 — Voice Field Assistant](docs/how-to/08-voice-field-assistant.md) | Real-time speech Q&A grounded in equipment manuals | GPT-4o Realtime, AI Search, WebSocket, Playwright |
| [09 — Competitive Intelligence Dashboard](docs/how-to/09-competitive-intelligence-dashboard.md) | Scheduled Bing search + trend charts → Cosmos DB dashboard | GPT-4.1, WebSearchTool, CodeInterpreterTool, Cosmos DB |
| [10 — Agentic Approval Workflow](docs/how-to/10-agentic-approval-workflow.md) | Human-in-the-loop approvals via Teams Adaptive Cards | GPT-5.4-mini, Foundry IQ, Graph API, Cosmos DB, Service Bus |
| [11 — Computer-Use Automator](docs/how-to/11-computer-use-automator.md) | GPT-5.4 drives a browser with screenshot → action loop | GPT-5.4, Responses API, Playwright, Key Vault |
| [12 — Multimodal Quality Inspector](docs/how-to/12-multimodal-quality-inspector.md) | IoT camera images → GPT-5.4 vision → defect detection + alerts | GPT-5.4, IoT Hub, Event Hubs, AI Search, Cosmos DB |

### Recommended Learning Path

**Week 1–2 (foundations):**
Start with [01 — Ask My Docs](docs/how-to/01-ask-my-docs.md) → [02 — Meeting Minutes Agent](docs/how-to/02-meeting-minutes-agent.md) → [04 — Policy Chatbot](docs/how-to/04-policy-chatbot.md)

**Week 3–4 (agents + tools):**
[03 — Email Triage](docs/how-to/03-email-triage-agent.md) → [05 — Contract Analyzer](docs/how-to/05-contract-clause-analyzer.md) → [06 — Incident Responder](docs/how-to/06-multi-agent-incident-responder.md)

**Month 2 (production patterns):**
[07 — Pipeline QA](docs/how-to/07-data-pipeline-qa-agent.md) → [09 — Intel Dashboard](docs/how-to/09-competitive-intelligence-dashboard.md) → [10 — Approval Workflow](docs/how-to/10-agentic-approval-workflow.md)

**Month 3 (advanced):**
[08 — Voice Assistant](docs/how-to/08-voice-field-assistant.md) → [12 — Quality Inspector](docs/how-to/12-multimodal-quality-inspector.md) → [11 — Computer Use](docs/how-to/11-computer-use-automator.md)
