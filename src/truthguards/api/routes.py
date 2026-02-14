"""API routes for TruthGuards."""

from fastapi import APIRouter, Depends, HTTPException, status

from truthguards.api.schemas import (
    GuardrailCreate,
    GuardrailCreated,
    GuardrailResponse,
    HealthResponse,
    ModelsResponse,
    SearchRequest,
    SearchResponse,
)
from truthguards.core.config import get_settings
from truthguards.core.weaviate_client import WeaviateClient, get_weaviate_client

router = APIRouter()


def get_client() -> WeaviateClient:
    """Dependency to get Weaviate client."""
    return get_weaviate_client()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(client: WeaviateClient = Depends(get_client)) -> HealthResponse:
    """Check the health of the service."""
    try:
        # Try to access Weaviate
        client.client.is_ready()
        weaviate_connected = True
    except Exception:
        weaviate_connected = False

    return HealthResponse(
        status="healthy" if weaviate_connected else "degraded",
        weaviate_connected=weaviate_connected,
    )


@router.get("/models", response_model=ModelsResponse, tags=["Configuration"])
async def list_models() -> ModelsResponse:
    """List available LLM models."""
    settings = get_settings()
    return ModelsResponse(models=settings.models)


@router.post(
    "/guardrails",
    response_model=GuardrailCreated,
    status_code=status.HTTP_201_CREATED,
    tags=["Guardrails"],
)
async def create_guardrail(
    guardrail: GuardrailCreate,
    client: WeaviateClient = Depends(get_client),
) -> GuardrailCreated:
    """
    Add a new guardrail to the database.

    This endpoint stores a guardrail that will be retrieved when searching
    for prompts similar to the one provided.
    """
    settings = get_settings()

    # Validate model name if models are configured
    if settings.models and guardrail.model_name not in settings.models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model name. Available models: {settings.models}",
        )

    try:
        guardrail_id = client.add_guardrail(
            prompt=guardrail.prompt,
            model_name=guardrail.model_name,
            guardrails=guardrail.guardrails,
        )
        return GuardrailCreated(id=guardrail_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create guardrail: {str(e)}",
        )


@router.post("/guardrails/search", response_model=SearchResponse, tags=["Guardrails"])
async def search_guardrails(
    search: SearchRequest,
    client: WeaviateClient = Depends(get_client),
) -> SearchResponse:
    """
    Search for relevant guardrails using hybrid search.

    This endpoint uses a combination of keyword and semantic search to find
    guardrails that are relevant to the provided prompt.
    """
    try:
        results = client.search_guardrails(
            prompt=search.prompt,
            model_name=search.model_name,
            limit=search.limit,
        )

        return SearchResponse(
            results=[
                GuardrailResponse(
                    id=r.id,
                    prompt=r.prompt,
                    model_name=r.model_name,
                    guardrails=r.guardrails,
                    score=r.score,
                )
                for r in results
            ],
            count=len(results),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/guardrails/{guardrail_id}", response_model=GuardrailResponse, tags=["Guardrails"])
async def get_guardrail(
    guardrail_id: str,
    client: WeaviateClient = Depends(get_client),
) -> GuardrailResponse:
    """Get a specific guardrail by ID."""
    result = client.get_guardrail(guardrail_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guardrail not found",
        )
    return GuardrailResponse(
        id=result.id,
        prompt=result.prompt,
        model_name=result.model_name,
        guardrails=result.guardrails,
        score=result.score,
    )


@router.delete(
    "/guardrails/{guardrail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Guardrails"],
)
async def delete_guardrail(
    guardrail_id: str,
    client: WeaviateClient = Depends(get_client),
) -> None:
    """Delete a guardrail by ID."""
    success = client.delete_guardrail(guardrail_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guardrail not found",
        )
