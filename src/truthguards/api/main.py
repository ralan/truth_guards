"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from truthguards.api.routes import router
from truthguards.core.config import get_settings
from truthguards.core.weaviate_client import get_weaviate_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup: connect to Weaviate
    client = get_weaviate_client()
    try:
        client.connect()
    except Exception as e:
        print(f"Warning: Could not connect to Weaviate: {e}")

    yield

    # Shutdown: close Weaviate connection
    client.close()


app = FastAPI(
    title="TruthGuards API",
    description="""
TruthGuards is a RAG-based guardrail retrieval system for AI agents.

It helps mitigate LLM hallucinations by storing and retrieving relevant textual
guardrails based on the prompt being processed. Instead of adding all guardrails
to every prompt, only the most relevant ones are retrieved using hybrid search
(combining keyword and semantic similarity).

## Features

- **Add Guardrails**: Store guardrails with associated prompts and model names
- **Search Guardrails**: Find relevant guardrails using hybrid search
- **Model Filtering**: Strict filtering by LLM model name
- **Hybrid Search**: Combines BM25 keyword search with vector semantic search
""",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware for Streamlit and other frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


# Also include routes at root for convenience
app.include_router(router)


def run():
    """Run the API server."""
    settings = get_settings()
    uvicorn.run(
        "truthguards.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=True,
    )


if __name__ == "__main__":
    run()
