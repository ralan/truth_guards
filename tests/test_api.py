"""Tests for the FastAPI API endpoints."""

import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_healthy(self, test_client, mock_weaviate_module):
        """Test health check when Weaviate is connected."""
        mock_weaviate_module.client.is_ready.return_value = True

        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["weaviate_connected"] is True

    def test_health_check_degraded(self, test_client, mock_weaviate_module):
        """Test health check when Weaviate is disconnected."""
        mock_weaviate_module.client.is_ready.side_effect = Exception("Connection failed")

        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["weaviate_connected"] is False


class TestModelsEndpoint:
    """Tests for the models endpoint."""

    def test_list_models(self, test_client, patched_settings):
        """Test listing available models."""
        response = test_client.get("/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "gpt-4" in data["models"]
        assert "claude-3-opus" in data["models"]


class TestGuardrailsEndpoints:
    """Tests for guardrail CRUD endpoints."""

    def test_create_guardrail(self, test_client, mock_weaviate_module, patched_settings):
        """Test creating a new guardrail."""
        response = test_client.post(
            "/guardrails",
            json={
                "prompt": "What is the capital of France?",
                "model_name": "gpt-4",
                "guardrails": "Always verify factual information.",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["id"] == "new-guardrail-id"
        assert data["message"] == "Guardrail created successfully"

    def test_create_guardrail_invalid_model(self, test_client, patched_settings):
        """Test creating guardrail with invalid model name."""
        response = test_client.post(
            "/guardrails",
            json={
                "prompt": "Test prompt",
                "model_name": "invalid-model",
                "guardrails": "Test guardrails",
            },
        )

        assert response.status_code == 400
        assert "Invalid model name" in response.json()["detail"]

    def test_search_guardrails(self, test_client, mock_weaviate_module):
        """Test searching for guardrails."""
        response = test_client.post(
            "/guardrails/search",
            json={
                "prompt": "Tell me about Paris",
                "model_name": "gpt-4",
                "limit": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["score"] == 0.95

    def test_search_guardrails_no_results(self, test_client, mock_weaviate_module):
        """Test searching when no results found."""
        mock_weaviate_module.search_guardrails.return_value = []

        response = test_client.post(
            "/guardrails/search",
            json={
                "prompt": "Unrelated query",
                "model_name": "gpt-4",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []

    def test_get_guardrail(self, test_client, mock_weaviate_module):
        """Test getting a guardrail by ID."""
        response = test_client.get("/guardrails/test-id-1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-id-1"
        assert data["model_name"] == "gpt-4"

    def test_get_guardrail_not_found(self, test_client, mock_weaviate_module):
        """Test getting a non-existent guardrail."""
        mock_weaviate_module.get_guardrail.return_value = None

        response = test_client.get("/guardrails/non-existent-id")

        assert response.status_code == 404

    def test_delete_guardrail(self, test_client, mock_weaviate_module):
        """Test deleting a guardrail."""
        response = test_client.delete("/guardrails/test-id-1")

        assert response.status_code == 204

    def test_delete_guardrail_not_found(self, test_client, mock_weaviate_module):
        """Test deleting a non-existent guardrail."""
        mock_weaviate_module.delete_guardrail.return_value = False

        response = test_client.delete("/guardrails/non-existent-id")

        assert response.status_code == 404


class TestAPIV1Prefix:
    """Tests for API v1 prefixed endpoints."""

    def test_v1_health(self, test_client, mock_weaviate_module):
        """Test health endpoint with v1 prefix."""
        mock_weaviate_module.client.is_ready.return_value = True

        response = test_client.get("/api/v1/health")

        assert response.status_code == 200

    def test_v1_models(self, test_client, patched_settings):
        """Test models endpoint with v1 prefix."""
        response = test_client.get("/api/v1/models")

        assert response.status_code == 200
