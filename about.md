## Inspiration

Every AI agent faces the same enemy: **hallucinations**. The common solution is adding guardrails to prompts—but here's the problem:

$$\text{More guardrails} = \text{Longer prompts} = \text{Higher latency} + \text{Higher cost}$$

We asked ourselves: *What if AI agents could learn from each other's mistakes?*

Humans don't rediscover fire every generation—we build on collective knowledge. Why should AI agents be different? This sparked **TruthGuards**: a shared memory system where agents contribute and retrieve only the guardrails relevant to their specific queries.

The hackathon theme "self-improving AI agents" was the perfect match—self-improvement doesn't have to be individual. Agents can improve *collectively*.

## What it does

TruthGuards enables **self-improving AI agents** through collective learning:

1. **Agent A** encounters a hallucination about medical advice → adds a guardrail
2. **Agent B** (anywhere in the world) asks a health question → retrieves that guardrail automatically
3. The more agents use the system, the smarter **everyone** becomes

The retrieval uses **hybrid search** combining:
- **BM25 (keyword matching)**: Finds exact term matches
- **Vector search (semantic similarity)**: Finds conceptually related guardrails

$$\text{Score} = \alpha \cdot \text{VectorScore} + (1-\alpha) \cdot \text{BM25Score}$$

Guardrails are filtered by LLM model (GPT-4, Claude, etc.) because different models need different guidance.

## How we built it

**Architecture:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│   FastAPI API   │────▶│    Weaviate     │
└─────────────────┘     └─────────────────┘     │  (Vector DB)    │
                              ▲                 └─────────────────┘
                              │
                        ┌─────────────────┐
                        │   MCP Server    │
                        └─────────────────┘
```

**Tech Stack:**
- **Python 3.12 + FastAPI** — REST API with automatic OpenAPI docs
- **Weaviate + text2vec-transformers** — Hybrid search with built-in embeddings (no external API keys needed)
- **MCP Server** — Direct integration with Claude and other AI assistants
- **Streamlit** — Web interface for adding/searching guardrails
- **Docker Compose** — One-command deployment of all services

**Development approach:** We used Claude Code to accelerate development—planning the architecture, implementing modules, and debugging Docker issues collaboratively.

## Challenges we ran into

**1. Weaviate Version Mismatch**
The `weaviate-client` v4 library requires Weaviate ≥1.27.0. We started with v1.24.1 and got cryptic errors. Debugging this taught us to always check version compatibility first.

**2. Docker Networking Gotcha**
The app couldn't connect to Weaviate inside Docker because config used `localhost`. Inside containers, services must reference each other by Docker service names (`weaviate`). We created separate configs for local vs. Docker environments.

**3. Transformer Cold Start**
The ML model takes 30-60 seconds to load. Early requests failed. We implemented health checks and graceful degradation to handle the initialization period.

**4. Search Quality Tuning**
Pure keyword search missed semantic matches ("hack wifi" ≠ "unauthorized access"). Pure vector search returned irrelevant results. Hybrid search with $\alpha = 0.5$ balanced both approaches perfectly.

## Accomplishments that we're proud of

- **Complete working system** — API, Web UI, MCP server, all dockerized and deployable
- **True hybrid search** — Not just vector similarity, but intelligent combination of keyword + semantic matching
- **Zero external dependencies** — Self-contained embeddings, no OpenAI/external API keys required
- **Production-ready** — Health checks, proper error handling, comprehensive tests
- **Multi-interface** — REST API for programmatic access, MCP for AI assistants, Streamlit for humans
- **Built in one day** — From idea to deployed system at truthguards.live

## What we learned

1. **RAG isn't just for documents** — It's powerful for dynamic, community-driven knowledge bases
2. **Self-improvement can be collective** — Agents don't need to learn individually; shared knowledge multiplies everyone's capabilities
3. **Hybrid search > pure vector search** — Real-world retrieval needs both keyword precision and semantic understanding
4. **Docker Compose is magic** — Complex multi-service architectures become one-command deployments
5. **AI-assisted development works** — Claude Code helped us move from concept to production remarkably fast

## What's next for TruthGuards

- **Guardrail effectiveness scoring** — Upvote/downvote system to surface the best guardrails
- **Automatic guardrail generation** — Detect hallucination patterns and suggest guardrails automatically
- **Enterprise multi-tenancy** — Private guardrail databases for companies with sensitive data
- **Analytics dashboard** — Insights into which guardrails are most retrieved and effective
- **Guardrail categories** — Organize by domain (medical, legal, financial, etc.)
- **API rate limiting & auth** — Production hardening for public deployment

---

*TruthGuards: Because the best way to prevent mistakes is to learn from everyone's mistakes.*
