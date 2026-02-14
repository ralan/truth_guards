"""Tests for the Weaviate client."""

from unittest.mock import MagicMock, patch

import pytest


class TestWeaviateClient:
    """Tests for WeaviateClient class."""

    def test_client_initialization(self):
        """Test client initialization with default settings."""
        with patch("truthguards.core.weaviate_client.get_settings") as mock_settings:
            mock_settings.return_value.weaviate.host = "localhost"
            mock_settings.return_value.weaviate.port = 8080
            mock_settings.return_value.weaviate.grpc_port = 50051

            from truthguards.core.weaviate_client import WeaviateClient

            client = WeaviateClient()

            assert client.host == "localhost"
            assert client.port == 8080
            assert client.grpc_port == 50051

    def test_client_custom_settings(self):
        """Test client initialization with custom settings."""
        with patch("truthguards.core.weaviate_client.get_settings"):
            from truthguards.core.weaviate_client import WeaviateClient

            client = WeaviateClient(
                host="custom-host",
                port=9090,
                grpc_port=60051,
            )

            assert client.host == "custom-host"
            assert client.port == 9090
            assert client.grpc_port == 60051


class TestGuardrailResult:
    """Tests for GuardrailResult dataclass."""

    def test_guardrail_result_creation(self):
        """Test creating a GuardrailResult."""
        from truthguards.core.weaviate_client import GuardrailResult

        result = GuardrailResult(
            id="test-id",
            prompt="Test prompt",
            model_name="gpt-4",
            guardrails="Test guardrails",
            score=0.95,
        )

        assert result.id == "test-id"
        assert result.prompt == "Test prompt"
        assert result.model_name == "gpt-4"
        assert result.guardrails == "Test guardrails"
        assert result.score == 0.95


class TestWeaviateClientMethods:
    """Tests for WeaviateClient methods using mocks."""

    @pytest.fixture
    def mock_client(self):
        """Create a WeaviateClient with mocked connection."""
        with patch("truthguards.core.weaviate_client.get_settings") as mock_settings:
            mock_settings.return_value.weaviate.host = "localhost"
            mock_settings.return_value.weaviate.port = 8080
            mock_settings.return_value.weaviate.grpc_port = 50051
            mock_settings.return_value.search.default_limit = 5
            mock_settings.return_value.search.alpha = 0.5

            from truthguards.core.weaviate_client import WeaviateClient

            client = WeaviateClient()

            # Mock the internal client
            mock_weaviate = MagicMock()
            client._client = mock_weaviate

            yield client

    def test_add_guardrail_calls_insert(self, mock_client):
        """Test that add_guardrail calls collection insert."""
        mock_collection = MagicMock()
        mock_client._client.collections.get.return_value = mock_collection

        result_id = mock_client.add_guardrail(
            prompt="Test prompt",
            model_name="gpt-4",
            guardrails="Test guardrails",
        )

        mock_collection.data.insert.assert_called_once()
        assert result_id is not None

    def test_search_guardrails_calls_hybrid(self, mock_client):
        """Test that search_guardrails calls hybrid query."""
        mock_collection = MagicMock()
        mock_client._client.collections.get.return_value = mock_collection

        # Mock search results
        mock_obj = MagicMock()
        mock_obj.uuid = "test-uuid"
        mock_obj.properties = {
            "prompt": "Test",
            "model_name": "gpt-4",
            "guardrails": "Test guardrails",
        }
        mock_obj.metadata.score = 0.9

        mock_result = MagicMock()
        mock_result.objects = [mock_obj]
        mock_collection.query.hybrid.return_value = mock_result

        results = mock_client.search_guardrails(
            prompt="Test query",
            model_name="gpt-4",
        )

        mock_collection.query.hybrid.assert_called_once()
        assert len(results) == 1
        assert results[0].score == 0.9

    def test_delete_guardrail_success(self, mock_client):
        """Test successful guardrail deletion."""
        mock_collection = MagicMock()
        mock_client._client.collections.get.return_value = mock_collection

        result = mock_client.delete_guardrail("test-id")

        assert result is True
        mock_collection.data.delete_by_id.assert_called_once_with("test-id")

    def test_delete_guardrail_failure(self, mock_client):
        """Test guardrail deletion when not found."""
        mock_collection = MagicMock()
        mock_collection.data.delete_by_id.side_effect = Exception("Not found")
        mock_client._client.collections.get.return_value = mock_collection

        result = mock_client.delete_guardrail("non-existent-id")

        assert result is False

    def test_close_connection(self, mock_client):
        """Test closing the connection."""
        mock_client.close()

        mock_client._client.close.assert_called_once()
        assert mock_client._client is None
