"""Pytest fixtures for TruthGuards tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_weaviate_client():
    """Create a mock Weaviate client."""
    mock_client = MagicMock()
    mock_client.is_ready.return_value = True
    return mock_client


@pytest.fixture
def mock_guardrail_results():
    """Sample guardrail search results."""
    from truthguards.core.weaviate_client import GuardrailResult

    return [
        GuardrailResult(
            id="test-id-1",
            prompt="What is the capital of France?",
            model_name="gpt-4",
            guardrails="Always verify factual information before responding.",
            score=0.95,
        ),
        GuardrailResult(
            id="test-id-2",
            prompt="Tell me about historical events",
            model_name="gpt-4",
            guardrails="Cross-reference historical facts with multiple sources.",
            score=0.85,
        ),
    ]


@pytest.fixture
def mock_weaviate_module(mock_weaviate_client, mock_guardrail_results):
    """Patch the Weaviate client module."""
    mock_instance = MagicMock()
    mock_instance.client = mock_weaviate_client
    mock_instance.connect.return_value = None
    mock_instance.close.return_value = None
    mock_instance.add_guardrail.return_value = "new-guardrail-id"
    mock_instance.search_guardrails.return_value = mock_guardrail_results
    mock_instance.get_guardrail.return_value = mock_guardrail_results[0]
    mock_instance.delete_guardrail.return_value = True

    with patch("truthguards.api.routes.get_weaviate_client", return_value=mock_instance):
        with patch("truthguards.api.main.get_weaviate_client", return_value=mock_instance):
            yield mock_instance


@pytest.fixture
def test_client(mock_weaviate_module):
    """Create a test client for the FastAPI app."""
    from truthguards.api.main import app

    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    from truthguards.core.config import Settings

    return Settings(
        models=["gpt-4", "claude-3-opus", "gemini-pro"],
    )


@pytest.fixture
def patched_settings(mock_settings):
    """Patch get_settings to return mock settings."""
    with patch("truthguards.core.config.get_settings", return_value=mock_settings):
        with patch("truthguards.api.routes.get_settings", return_value=mock_settings):
            yield mock_settings
