# TruthGuards
### Collective Memory for Self-Improving AI Agents

---

## The Problem

| Without TruthGuards | With TruthGuards |
|---------------------|------------------|
| Every agent adds ALL guardrails to every prompt | Agents retrieve only RELEVANT guardrails |
| Prompts become bloated and expensive | Lean prompts, lower cost |
| Each agent learns in isolation | Agents learn from EACH OTHER |
| Same mistakes repeated globally | One fix benefits everyone |

**The Math:**
```
Traditional: Cost = Base + (All Guardrails × Every Query)
TruthGuards: Cost = Base + (Relevant Guardrails × Query)
```

---

## The Solution: Self-Improving Through Collective Learning

```
    Agent A (Tokyo)              Agent B (London)              Agent C (NYC)
         │                            │                            │
         │ adds medical               │ asks health                │ asks symptom
         │ guardrail                  │ question                   │ question
         ▼                            ▼                            ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │                     TruthGuards Database                        │
    │                    (Hybrid Search Engine)                       │
    │                                                                 │
    │   🔍 Semantic Search (understands meaning)                      │
    │   🔑 Keyword Search (finds exact matches)                       │
    │   🎯 Model Filter (GPT-4, Claude, etc.)                         │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
                    │                            │
                    ▼                            ▼
              Returns medical            Returns medical
              guardrail to B             guardrail to C
```

**One agent's learning → Everyone's improvement = Self-Improving AI Network**

---

## Live Demo: truthguards.live

| Interface | URL | Purpose |
|-----------|-----|---------|
| **Web UI** | truthguards.live:8501 | Human-friendly interface |
| **REST API** | truthguards.live:8000 | Programmatic access |
| **API Docs** | truthguards.live:8000/docs | Interactive documentation |
| **MCP Server** | Built-in | Direct Claude integration |

### API Example
```bash
# Add guardrail
POST /guardrails {"prompt": "medical question", "model": "gpt-4", "guardrails": "..."}

# Search (hybrid: keyword + semantic)
POST /guardrails/search {"prompt": "I have fever", "model": "gpt-4"}
→ Returns relevant medical guardrails with relevance scores
```

---

## Technical Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐
│  Streamlit   │───▶│   FastAPI    │───▶│  Weaviate + Transformers │
│   Web UI     │    │   REST API   │    │   (Hybrid Vector DB)     │
└──────────────┘    └──────────────┘    └──────────────────────────┘
                          ▲
                          │
                    ┌──────────────┐
                    │  MCP Server  │ ◀── Claude / AI Assistants
                    └──────────────┘
```

| Component | Technology | Why |
|-----------|------------|-----|
| API | FastAPI + Python 3.12 | Fast, async, auto-docs |
| Search | Weaviate Hybrid | Best of keyword + semantic |
| Embeddings | Sentence Transformers | Self-contained, no API keys |
| UI | Streamlit | Rapid prototyping |
| Deploy | Docker Compose | One-command deployment |
| AI Integration | MCP Protocol | Native Claude support |

---

## Why TruthGuards Wins

| Criteria | How We Deliver |
|----------|----------------|
| **Completion & Demo** | ✅ Full working system live at truthguards.live |
| **Self-Improving Agents** | ✅ Core concept: agents improve collectively |
| **Scalability** | ✅ Vector DB scales horizontally, Docker-ready |
| **Innovation** | ✅ Novel: shared guardrail memory + hybrid search |
| **Output Quality** | ✅ Tested: medical, legal, security queries work |
| **Presentation** | ✅ Clear problem → solution → demo flow |

---

## Key Differentiators

| Feature | TruthGuards | Traditional Approach |
|---------|-------------|---------------------|
| Guardrail Selection | Smart (relevant only) | Dumb (all or nothing) |
| Learning | Collective | Individual |
| Search | Hybrid (semantic + keyword) | Usually keyword only |
| Dependencies | Self-contained | Often needs OpenAI API |
| Deployment | One command | Complex setup |

---

## What's Next

1. **Guardrail Voting** — Community ranks effectiveness
2. **Auto-Generation** — Detect hallucinations → suggest guardrails
3. **Enterprise Mode** — Private databases for companies
4. **Analytics** — Which guardrails work best?

---

<div align="center">

## TruthGuards

**Self-improving AI agents learn from each other's mistakes.**

🌐 **truthguards.live** | 📦 **github.com/yourusername/truthguards**

*Because the best way to prevent mistakes is to learn from everyone's mistakes.*

</div>
