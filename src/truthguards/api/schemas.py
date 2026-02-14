"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field


class GuardrailCreate(BaseModel):
    """Request body for creating a new guardrail."""

    prompt: str = Field(..., description="The prompt pattern this guardrail applies to")
    model_name: str = Field(..., description="The LLM model this guardrail is for")
    guardrails: str = Field(..., description="The guardrail text to add to prompts")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "What is the capital of France?",
                    "model_name": "gpt-4",
                    "guardrails": "Always verify factual information before responding. If uncertain, clearly state that the information should be verified.",
                }
            ]
        }
    }


class GuardrailResponse(BaseModel):
    """Response model for a single guardrail."""

    id: str = Field(..., description="Unique identifier of the guardrail")
    prompt: str = Field(..., description="The prompt pattern this guardrail applies to")
    model_name: str = Field(..., description="The LLM model this guardrail is for")
    guardrails: str = Field(..., description="The guardrail text")
    score: float = Field(..., description="Relevance score from hybrid search (0-1)")


class GuardrailCreated(BaseModel):
    """Response after creating a guardrail."""

    id: str = Field(..., description="Unique identifier of the created guardrail")
    message: str = Field(default="Guardrail created successfully")


class SearchRequest(BaseModel):
    """Request body for searching guardrails."""

    prompt: str = Field(..., description="The prompt to search for relevant guardrails")
    model_name: str = Field(..., description="Filter by LLM model")
    limit: int = Field(default=5, ge=1, le=100, description="Maximum number of results")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "Tell me about historical events",
                    "model_name": "gpt-4",
                    "limit": 5,
                }
            ]
        }
    }


class SearchResponse(BaseModel):
    """Response for guardrail search."""

    results: list[GuardrailResponse] = Field(..., description="List of matching guardrails")
    count: int = Field(..., description="Number of results returned")


class ModelsResponse(BaseModel):
    """Response listing available models."""

    models: list[str] = Field(..., description="List of available LLM model names")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    weaviate_connected: bool = Field(..., description="Whether Weaviate is connected")
