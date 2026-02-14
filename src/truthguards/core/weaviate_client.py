"""Weaviate client for storing and searching guardrails."""

import uuid
from dataclasses import dataclass
from typing import Any

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Filter, MetadataQuery

from truthguards.core.config import get_settings

COLLECTION_NAME = "Guardrail"


@dataclass
class GuardrailResult:
    """Result from guardrail search."""

    id: str
    prompt: str
    model_name: str
    guardrails: str
    score: float


class WeaviateClient:
    """Client for interacting with Weaviate vector database."""

    def __init__(self, host: str | None = None, port: int | None = None, grpc_port: int | None = None):
        """Initialize Weaviate client."""
        settings = get_settings()
        self.host = host or settings.weaviate.host
        self.port = port or settings.weaviate.port
        self.grpc_port = grpc_port or settings.weaviate.grpc_port
        self._client: weaviate.WeaviateClient | None = None

    def connect(self) -> None:
        """Connect to Weaviate instance."""
        self._client = weaviate.connect_to_local(
            host=self.host,
            port=self.port,
            grpc_port=self.grpc_port,
        )
        self._ensure_collection()

    def close(self) -> None:
        """Close the Weaviate connection."""
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self) -> weaviate.WeaviateClient:
        """Get the Weaviate client, connecting if necessary."""
        if self._client is None:
            self.connect()
        return self._client  # type: ignore

    def _ensure_collection(self) -> None:
        """Ensure the Guardrail collection exists."""
        if self.client.collections.exists(COLLECTION_NAME):
            return

        self.client.collections.create(
            name=COLLECTION_NAME,
            vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
            properties=[
                Property(
                    name="prompt",
                    data_type=DataType.TEXT,
                    description="The prompt or question pattern this guardrail applies to",
                ),
                Property(
                    name="model_name",
                    data_type=DataType.TEXT,
                    description="The LLM model this guardrail is for",
                    skip_vectorization=True,  # Don't include model name in vector
                ),
                Property(
                    name="guardrails",
                    data_type=DataType.TEXT,
                    description="The guardrail text to add to prompts",
                ),
            ],
        )

    def add_guardrail(self, prompt: str, model_name: str, guardrails: str) -> str:
        """
        Add a new guardrail to the database.

        Args:
            prompt: The prompt pattern this guardrail applies to
            model_name: The LLM model this guardrail is for
            guardrails: The guardrail text

        Returns:
            The UUID of the created guardrail
        """
        collection = self.client.collections.get(COLLECTION_NAME)
        guardrail_id = str(uuid.uuid4())

        collection.data.insert(
            properties={
                "prompt": prompt,
                "model_name": model_name,
                "guardrails": guardrails,
            },
            uuid=guardrail_id,
        )

        return guardrail_id

    def search_guardrails(
        self,
        prompt: str,
        model_name: str,
        limit: int | None = None,
        alpha: float | None = None,
    ) -> list[GuardrailResult]:
        """
        Search for relevant guardrails using hybrid search.

        Args:
            prompt: The prompt to search for
            model_name: Filter by model name (strict filter)
            limit: Maximum number of results to return
            alpha: Balance between keyword (0) and vector (1) search

        Returns:
            List of matching guardrails with relevance scores
        """
        settings = get_settings()
        limit = limit or settings.search.default_limit
        alpha = alpha if alpha is not None else settings.search.alpha

        collection = self.client.collections.get(COLLECTION_NAME)

        # Hybrid search with strict model filter
        results = collection.query.hybrid(
            query=prompt,
            alpha=alpha,
            limit=limit,
            filters=Filter.by_property("model_name").equal(model_name),
            return_metadata=MetadataQuery(score=True),
        )

        return [
            GuardrailResult(
                id=str(obj.uuid),
                prompt=obj.properties["prompt"],
                model_name=obj.properties["model_name"],
                guardrails=obj.properties["guardrails"],
                score=obj.metadata.score or 0.0,
            )
            for obj in results.objects
        ]

    def delete_guardrail(self, guardrail_id: str) -> bool:
        """
        Delete a guardrail by ID.

        Args:
            guardrail_id: The UUID of the guardrail to delete

        Returns:
            True if deleted, False if not found
        """
        collection = self.client.collections.get(COLLECTION_NAME)
        try:
            collection.data.delete_by_id(guardrail_id)
            return True
        except Exception:
            return False

    def get_guardrail(self, guardrail_id: str) -> GuardrailResult | None:
        """
        Get a guardrail by ID.

        Args:
            guardrail_id: The UUID of the guardrail

        Returns:
            The guardrail if found, None otherwise
        """
        collection = self.client.collections.get(COLLECTION_NAME)
        try:
            obj = collection.query.fetch_object_by_id(guardrail_id)
            if obj is None:
                return None
            return GuardrailResult(
                id=str(obj.uuid),
                prompt=obj.properties["prompt"],
                model_name=obj.properties["model_name"],
                guardrails=obj.properties["guardrails"],
                score=1.0,
            )
        except Exception:
            return None


# Singleton instance for convenience
_client: WeaviateClient | None = None


def get_weaviate_client() -> WeaviateClient:
    """Get the singleton Weaviate client instance."""
    global _client
    if _client is None:
        _client = WeaviateClient()
    return _client
