# 12 AI Projects to Get You Dangerous — CSU Cloud & AI Onboarding

**Who this is for:** You just joined CSU as a Cloud Solution Architect. You know cloud. You don't know AI yet.  
**What this gives you:** Ramp-up projects that double as customer-ready demos.  
**Platform:** Microsoft Foundry — everything here runs on it. Not standalone Azure OpenAI. Not third-party. Foundry.  
**Models:** GPT-5.5, GPT-5.4 series, GPT-4.1 series, o-series reasoning models

---

## Why You Should Care

You need two things in your first 90 days: confidence that you can actually build with the AI stack, and something real to show a customer who's sitting across the table asking "so what can this do?"

Slides won't get you there. A working demo will.

That's what these 12 ideas are. Some are personal demo assets — things you build once and pull up in every meeting. Others are co-build templates you clone, swap in a customer's data, and deploy in a POC sprint. The roadmap at the bottom tells you what order to tackle them.

---

## At a Glance

| # | Idea | Type | Impact | Difficulty | Effort |
|---|------|------|--------|------------|--------|
| 1 | Ask My Docs — RAG Starter | Demo asset | ⭐⭐⭐⭐ | ⭐⭐ | 1-2 days |
| 2 | Meeting Minutes Agent | Demo asset | ⭐⭐⭐⭐ | ⭐⭐ | 2-3 days |
| 3 | Customer Email Triage Agent | Co-build | ⭐⭐⭐⭐⭐ | ⭐⭐ | ~1 week |
| 4 | Internal Policy Chatbot | Co-build | ⭐⭐⭐⭐ | ⭐⭐ | ~1 week |
| 5 | Contract Clause Analyzer | Co-build | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ~2 weeks |
| 6 | Multi-Agent Incident Responder | Demo asset | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ~2 weeks |
| 7 | Data Pipeline QA Agent | Co-build | ⭐⭐⭐⭐ | ⭐⭐⭐ | 2-3 weeks |
| 8 | Voice-Enabled Field Assistant | Demo asset | ⭐⭐⭐⭐ | ⭐⭐⭐ | 2-3 weeks |
| 9 | Competitive Intelligence Dashboard | Co-build | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 3-4 weeks |
| 10 | Agentic Workflow for Approvals | Co-build | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 4-6 weeks |
| 11 | Computer-Use Process Automator | Demo asset | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 4-6 weeks |
| 12 | Multi-Modal Quality Inspector | Co-build | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 6-8 weeks |

They're ordered roughly by difficulty. Start at the top.

---

## 1. Ask My Docs — RAG Starter Kit

**Demo asset · 1-2 days**

Every customer you'll ever meet will ask some version of the same question: "Can AI search our documents?" This is your answer. Not a slide about RAG — a working demo you pull up on your laptop.

Set up a prompt agent in Foundry Agent Service, enable File Search, upload 10-20 PDFs (Azure docs, a customer's annual report, whatever fits the meeting). Now you've got a grounded chatbot that answers questions and shows where it found the answer.

**You'll use:** Foundry project + prompt agent, File Search tool, GPT-4.1-mini (fast and cheap) or GPT-5.4-mini (better reasoning), Azure Blob Storage.

**What you'll actually learn:** How Foundry projects work, how agents get created, how File Search chunks documents under the hood, and why grounding quality varies depending on your docs.

**Once that's working:** Swap out File Search for Azure AI Search with custom chunking and text-embedding-3-large vectors. That's the jump from "managed RAG" to "I understand the full stack." Worth doing before your first customer meeting.

---

## 2. Meeting Minutes Agent

**Demo asset · 2-3 days**

This is the demo where people lean forward and say "wait, I actually want that."

Record a Teams meeting (or grab a sample audio file). Run it through Foundry audio models for transcription. Hand the transcript to a prompt agent that pulls out action items, decisions, and a summary. Output: structured markdown or JSON.

Everyone sits in too many meetings. Everyone hates writing up the notes. When you show this working live — audio in, structured notes out — it clicks instantly.

**You'll use:** Foundry, GPT-4o audio or Whisper (transcription), GPT-4.1-mini (summarization agent), Foundry Agent Service. Optional: Azure Functions with a timer trigger if you want batch processing.

**The real lesson here:** How to chain model outputs (audio model → text model), and how to write prompts that extract structured data reliably. You'll also discover that prompt engineering for extraction is a different beast than prompt engineering for chat.

---

## 3. Customer Email Triage Agent

**Co-build template · ~1 week**

Every company with a support inbox is drowning. They know it. You know it.

Build an agent that reads incoming emails or support tickets from a queue, classifies them by urgency and topic, drafts a response, and routes to the right team. The agent uses function calling to hit the customer's ticketing API and pulls response templates from a knowledge base.

The trick here is multi-model routing: GPT-4.1-mini for classification (fast, cheap, accurate enough), GPT-5.4-mini for drafting the actual response (needs to sound good). Don't use an expensive model for a classification task. Don't use a cheap model to write customer-facing text. Match the model to the job.

**You'll use:** Foundry (prompt agent with function calling), GPT-4.1-mini + GPT-5.4-mini, Azure Service Bus (queue ingestion), Azure AI Search + Foundry IQ (response templates), Azure Cosmos DB (ticket state and routing history).

**Why this works as a co-build:** Almost every customer has this problem, regardless of industry. First-response times go from hours to minutes. Misrouted tickets drop dramatically once you've tuned the classification categories to their domain. This is one of the easiest POCs to propose because the ROI is so visible.

---

## 4. Internal Policy Chatbot

**Co-build template · ~1 week**

"How many vacation days do I have left?" "What's the approval process for a new laptop?" "Can I expense this?"

HR and IT helpdesks field thousands of these every month. The answers are all in a 200-page PDF somewhere. Nobody reads the PDF.

This one uses Foundry IQ — the turnkey RAG option that handles chunking and embedding for you. You bring the documents, Foundry does the rest. Point it at a customer's HR policies, IT guidelines, or compliance docs, and employees get cited answers instead of "please refer to section 4.2.1 of the employee handbook."

The difference between this and Idea 1: Idea 1 teaches you how RAG works under the hood. This one teaches you when to skip all that and use the managed option. (Spoiler: start with Foundry IQ. Graduate to custom RAG when you need control over chunking.)

**You'll use:** Foundry with Foundry IQ, GPT-4.1-mini (handles policy Q&A well at low cost), Microsoft Entra ID (employees only — you need auth), Azure App Service (chat UI).

**The skill you're building:** Knowing when the managed path is the right call. Customers love hearing "you don't need to build a pipeline for this." It saves them months.

---

## 5. Contract Clause Analyzer

**Co-build template · ~2 weeks**

Legal review runs at $500/hour. That's not a metaphor. That's the invoice.

Build an agent with Code Interpreter that takes a contract (PDF or Word), extracts clauses, flags risky language against a configurable ruleset, and spits out a risk summary with clause-by-clause annotations. Think "redline review assistant" — not replacing lawyers, but cutting the time they spend on routine clause identification in half.

Here's why this one opens doors: when you demo an agent that correctly flags an indemnification clause with unusual liability caps, you get attention from the CFO and General Counsel — not just IT. Legal teams spend the majority of their contract review time on standard clause identification. That's the work this automates.

**You'll use:** Foundry (prompt agent with Code Interpreter), GPT-5.4 (contracts are long — you want the full document in the 1M token context window, not chunked), Azure AI Document Intelligence (for scanned contract PDFs), Blob Storage (contract repo), Cosmos DB (clause library and risk rules).

**What makes this hard:** Long-context prompt design is its own discipline. You'll learn to write prompts that keep the model focused across a 40-page document. You'll also learn structured output with confidence scoring — and how to talk to legal teams about AI without terrifying them.

---

## 6. Multi-Agent Incident Responder

**Demo asset · ~2 weeks**

This is your "I didn't know you could do that" demo. Most customers have heard the phrase "multi-agent systems." Almost none have seen one running.

Three agents, one production incident:

- **Agent 1 (Diagnostician)** reads logs and metrics from Application Insights
- **Agent 2 (Researcher)** searches runbooks and past incident reports
- **Agent 3 (Communicator)** drafts stakeholder updates

All three work concurrently, orchestrated as a workflow agent in Foundry. The insight here: MTTR drops when diagnosis and communication happen in parallel instead of one person doing everything sequentially.

**You'll use:** Foundry (workflow agent orchestrating 3 prompt agents), Foundry Agent Service, GPT-5.4-mini (fast reasoning for log analysis), Azure Monitor / Application Insights (data source via MCP or function calling), Azure AI Search (runbook and incident history index). If you want code-level control over orchestration: Microsoft Agent Framework.

**This is the project where multi-agent orchestration stops being abstract.** You'll implement the concurrent fan-out pattern, connect agents to live Azure data sources, and — most importantly — start understanding when the Agent Framework SDK is the right tool vs. when Foundry's built-in orchestration is enough. Save this demo for platform engineering and DevOps conversations.

---

## 7. Data Pipeline QA Agent

**Co-build template · 2-3 weeks**

Nobody wants to be the person who finds bad data in a dashboard two days after the pipeline broke. And yet.

Build an agent that monitors data pipelines (Data Factory, Synapse, Fabric) and runs automated quality checks when a pipeline completes. It inspects output data for null spikes, schema drift, distribution shifts — and either auto-remediates or pings the data team with a diagnosis.

The interesting design decision: use GPT-4.1-mini for describing anomalies (it's fast and the descriptions don't need to be creative), but use codex-mini for generating remediation scripts (it's optimized for code). This is multi-model routing again — same pattern as Idea 3, different context.

**You'll use:** Foundry (prompt agent with Code Interpreter for stats), GPT-4.1-mini + codex-mini, Azure Functions (triggered by Cosmos DB change feed or Event Grid on pipeline completion), Cosmos DB (run metadata and quality scores), Data Factory or Microsoft Fabric.

**What makes this one sticky for customers:** Data quality issues are expensive. Not in a hand-wavy way — Gartner puts the average cost at $12.9M/year for enterprises. Catching anomalies in minutes instead of days prevents real downstream damage. Data platform teams tend to get excited about this one fast.

---

## 8. Voice-Enabled Field Assistant

**Demo asset · 2-3 weeks**

"What's the torque spec for the Model 7200 compressor valve?"

Imagine asking that out loud — hands full, standing next to the equipment — and getting a spoken answer grounded in the actual equipment manual. That's this project.

It's a mobile-friendly web app built on GPT-4o Realtime for low-latency voice. Speech in, speech out. Field technicians don't have free hands to scroll through PDFs. Manufacturing and energy customers light up when they see their own technical docs answering voice queries.

A quick back-of-napkin number: field service calls where techs need remote expert support run $150-300 each. If a voice assistant handles even half of those from documentation alone, you're looking at six-figure annual savings for a mid-size operation.

**You'll use:** Foundry, GPT-4o Realtime, Azure AI Search (equipment manual index with text-embedding-3-large), Azure Container Apps (backend), App Service (mobile-optimized frontend), Blob Storage (manual PDFs and images).

**Bring this one to:** Manufacturing conversations. Energy. Logistics. Any customer with field workers and thick equipment manuals.

---

## 9. Competitive Intelligence Dashboard

**Co-build template · 3-4 weeks**

Strategy teams spend 15-20 hours a week manually scanning competitor websites, news feeds, SEC filings, and social media. They know it's a waste. They keep doing it because nobody's automated the alternative.

This agent does. It monitors those sources continuously, summarizes changes, spots trends, and feeds a dashboard. Marketing and strategy get a daily digest instead of 15 browser tabs.

The agent uses Bing Web Search grounding for real-time data and Code Interpreter to generate charts and trend analysis. You schedule it to run daily or weekly via Foundry Agent Service's API.

**You'll use:** Foundry (prompt agent with Web Search + Code Interpreter), GPT-5.4 (strong reasoning for synthesizing across disparate sources), Foundry Agent Service (scheduled runs), Cosmos DB (intelligence history), Container Apps (dashboard API), Static Web Apps (frontend), Azure Functions (scheduled trigger).

**What's new here vs. earlier projects:** Web grounding (pulling live data from the internet, not just internal docs), scheduled agent execution (agents that run on a clock, not on demand), and building a reporting layer on top of agent outputs. This is where you learn to make agents do ongoing work, not just answer one-off questions.

---

## 10. Agentic Workflow for Approvals

**Co-build template · 4-6 weeks**

Some things shouldn't be fully autonomous. This project teaches you why.

A workflow agent handles multi-step business approvals: purchase requests, access provisioning, change management tickets. The agent reads the request, checks it against policies (via Foundry IQ), routes to the right approver, follows up on stale approvals, and logs everything. But — and this is the design point — a human makes the actual decision. The agent prepares. The human approves.

Approval bottlenecks slow down procurement by days. Automated preparation, routing, and nagging cuts that cycle time dramatically. But the value here isn't just speed — it's the audit trail. Everything logged. Every step traceable.

**You'll use:** Foundry (workflow agent with branching logic and human-in-the-loop), Foundry Agent Service (hosting + state management), GPT-4.1-mini (fast policy checking), Foundry IQ (policy knowledge base), Service Bus (request ingestion), Cosmos DB (approval state and audit trail), Microsoft Graph API (Teams notifications), Entra ID (identity and RBAC).

**This is enterprise AI.** Messy. Stateful. Long-running processes that span days. Human-in-the-loop patterns. Microsoft Graph integration for notifications. If you want to understand why workflow agents exist as a distinct concept from prompt agents, build this.

---

## 11. Computer-Use Process Automator

**Demo asset · 4-6 weeks**

Every enterprise has at least one terrible legacy app that someone spends hours clicking through daily. No API. No integration points. Just a web UI and a person copy-pasting between two systems.

GPT-5.4 can see a screen, reason about UI elements, and take actions — click, type, scroll. Build an agent that automates a repetitive process in a legacy web app: filling out ERP forms, exporting reports from a vendor portal, doing data entry across systems that don't talk to each other.

When you demo this, people say "I didn't know AI could do that." Then they immediately think of three processes they want to automate. That's the conversation you want.

**You'll use:** Foundry, GPT-5.4 with computer-use capability (via Responses API), Container Apps (agent runtime with browser automation), Microsoft Agent Framework (code-level control over the computer-use loop), Azure Key Vault (credentials for legacy system access).

**Important:** Always demo with human-in-the-loop confirmation before the agent takes actions. An autonomous agent clicking through a production ERP system with no guardrails is a horror story, not a demo. The Responses API (the new agent API that replaced Assistants) gives you the control loop you need. Build the safety rails first, then the automation.

---

## 12. Multi-Modal Quality Inspector

**Co-build template · 6-8 weeks**

The hardest build on this list. Also the highest-value demo for manufacturing customers.

Cameras on a production line capture product images. Your agent analyzes them for defects using GPT-5.4's vision capabilities, cross-references against a defect catalog in Azure AI Search, and triggers alerts or line stops based on severity. Add Code Interpreter for statistical process control charts.

A defect that reaches a customer costs 5-10x more to address than catching it on the line. That math is what makes this project worth the complexity.

**You'll use:** Foundry (hosted agent with Microsoft Agent Framework), GPT-5.4 (vision + reasoning), Azure AI Search (defect catalog with image embeddings), Azure IoT Hub (camera feed ingestion), Container Apps (agent hosting), Cosmos DB (inspection history and SPC data), Event Hubs (real-time event streaming), Azure Monitor + Application Insights (agent observability).

**This is a portfolio piece.** Multi-modal input, real-time processing, IoT integration, hosted agents in Foundry — it touches everything. The architecture is complex because the problem is complex. Don't attempt this one until you've built at least 3-4 of the earlier ideas and have a real manufacturing customer to co-build with.

---

## Phased Roadmap

### Phase 1: First 90 Days — Get Your Hands Dirty

| Week | Build | Why |
|------|-------|-----|
| 1 | **Ask My Docs** | Foundry basics + RAG in a day. You'll reference this forever. |
| 2 | **Meeting Minutes Agent** | Audio models + prompt agents. Everyone relates to this one. |
| 3-4 | **Internal Policy Chatbot** | Foundry IQ. First co-build template you can adapt to any customer with internal docs. |
| 5-6 | **Customer Email Triage** | Function calling + multi-model routing. Strong cross-industry co-build. |
| 7-10 | **Multi-Agent Incident Responder** | Multi-agent orchestration. The project where everything clicks. |
| 11-12 | Polish + customize | Swap in customer-relevant data. Rehearse the storytelling. |

**By day 90:** 4-5 working demos, comfort with Foundry Agent Service, ability to spin up a customer POC in a week.

### Phase 2: Months 3-9 — Co-Build with Real Customers

Pick 2-3 based on who you're actually working with:

- **Contract Clause Analyzer** — legal/procurement customers
- **Data Pipeline QA Agent** — data platform customers
- **Voice-Enabled Field Assistant** — manufacturing/field service
- **Competitive Intelligence Dashboard** — marketing/strategy conversations

Each one teaches a different skill: long-context reasoning, event-driven agents, voice APIs, web grounding. Let your customer conversations guide the choice.

### Phase 3: Months 9-18 — The Hard Stuff

- **Agentic Workflow for Approvals** — enterprise workflow automation, human-in-the-loop
- **Computer-Use Process Automator** — bleeding edge, high wow factor
- **Multi-Modal Quality Inspector** — deep industry play, complex architecture

These are the projects that turn you from "the new CSA" into "the person I call when we need someone who's done this before."

---

## Architecture Patterns You'll Keep Using

You'll notice the same patterns showing up across these builds:

| Pattern | What it means | Where you'll see it |
|---------|---------------|---------------------|
| **Single prompt agent** | One agent, one job — Q&A, classification, summarization | 1, 2, 4 |
| **Agent + Function Calling** | The agent reads from or writes to external systems | 3, 5, 7 |
| **Workflow agent** | Multi-step process with branching or human approval gates | 6, 10 |
| **Hosted agent** | You need full code-level control over the orchestration loop | 11, 12 |
| **Foundry IQ** | Managed RAG — skip the pipeline, bring your docs | 4, 10 |
| **Azure AI Search + custom embeddings** | You need control over chunking, hybrid search, or image vectors | 1 (stretch), 8, 9, 12 |
| **Multi-model routing** | Cheap fast model for the easy work, expensive model for the hard work | 3, 7 |

---

## Which Model for What

Don't overthink this. Here's the cheat sheet:

| What you're doing | Use this | Why |
|-------------------|----------|-----|
| Classification, routing, simple extraction | GPT-4.1-mini | Fast, cheap, accurate enough for the job |
| General Q&A, summarization | GPT-4.1-mini or GPT-5.4-mini | Good quality without burning budget |
| Long documents (contracts, reports) | GPT-5.4 | 1M token context — fits entire docs without chunking |
| Hard reasoning, synthesis across sources | GPT-5.4 or GPT-5.5 | When getting it right matters more than getting it fast |
| Code generation | codex-mini or GPT-5.3-codex | Built for code. Use them for code. |
| Voice interaction | GPT-4o Realtime | Low-latency speech-in/speech-out |
| Vision / image analysis | GPT-5.4 | Strong multimodal reasoning |
| Embeddings | text-embedding-3-large | Best retrieval quality (text-embedding-3-small if budget is tight) |

---

## Go

The best demo is the one you've actually built and broken and fixed. Slides about RAG don't teach you what happens when chunking goes wrong. A contract analyzer that hallucinates clause numbers teaches you more about grounding than any training course ever will.

Build the first three this month. Not next month. This month.

---

*CSU Cloud & AI onboarding — May 2026*
