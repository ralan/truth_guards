"""Tests for the MCP server."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMCPTools:
    """Tests for MCP tool definitions."""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that tools are listed correctly."""
        with patch("truthguards.mcp.server.get_settings") as mock_settings:
            mock_settings.return_value.models = ["gpt-4", "claude-3-opus"]

            from truthguards.mcp.server import list_tools

            tools = await list_tools()

            assert len(tools) == 2

            tool_names = [t.name for t in tools]
            assert "add_guardrail" in tool_names
            assert "search_guardrails" in tool_names

    @pytest.mark.asyncio
    async def test_add_guardrail_tool_schema(self):
        """Test add_guardrail tool has correct schema."""
        with patch("truthguards.mcp.server.get_settings") as mock_settings:
            mock_settings.return_value.models = ["gpt-4"]

            from truthguards.mcp.server import list_tools

            tools = await list_tools()
            add_tool = next(t for t in tools if t.name == "add_guardrail")

            schema = add_tool.inputSchema
            assert schema["type"] == "object"
            assert "prompt" in schema["properties"]
            assert "model_name" in schema["properties"]
            assert "guardrails" in schema["properties"]
            assert set(schema["required"]) == {"prompt", "model_name", "guardrails"}

    @pytest.mark.asyncio
    async def test_search_guardrails_tool_schema(self):
        """Test search_guardrails tool has correct schema."""
        with patch("truthguards.mcp.server.get_settings") as mock_settings:
            mock_settings.return_value.models = ["gpt-4"]

            from truthguards.mcp.server import list_tools

            tools = await list_tools()
            search_tool = next(t for t in tools if t.name == "search_guardrails")

            schema = search_tool.inputSchema
            assert schema["type"] == "object"
            assert "prompt" in schema["properties"]
            assert "model_name" in schema["properties"]
            assert "limit" in schema["properties"]
            assert set(schema["required"]) == {"prompt", "model_name"}


class TestMCPToolCalls:
    """Tests for MCP tool call handlers."""

    @pytest.fixture
    def mock_weaviate(self):
        """Create a mock Weaviate client."""
        mock = MagicMock()
        mock.connect.return_value = None
        mock.add_guardrail.return_value = "new-id-123"
        return mock

    @pytest.mark.asyncio
    async def test_handle_add_guardrail_success(self, mock_weaviate):
        """Test successful add_guardrail call."""
        with patch("truthguards.mcp.server.get_settings") as mock_settings:
            mock_settings.return_value.models = ["gpt-4"]

            from truthguards.mcp.server import handle_add_guardrail

            result = await handle_add_guardrail(
                mock_weaviate,
                {
                    "prompt": "Test prompt",
                    "model_name": "gpt-4",
                    "guardrails": "Test guardrails",
                },
            )

            assert len(result) == 1
            assert "new-id-123" in result[0].text
            mock_weaviate.add_guardrail.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_add_guardrail_missing_args(self, mock_weaviate):
        """Test add_guardrail with missing arguments."""
        from truthguards.mcp.server import handle_add_guardrail

        result = await handle_add_guardrail(
            mock_weaviate,
            {"prompt": "Test prompt"},  # Missing model_name and guardrails
        )

        assert len(result) == 1
        assert "Missing required arguments" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_add_guardrail_invalid_model(self, mock_weaviate):
        """Test add_guardrail with invalid model name."""
        with patch("truthguards.mcp.server.get_settings") as mock_settings:
            mock_settings.return_value.models = ["gpt-4"]

            from truthguards.mcp.server import handle_add_guardrail

            result = await handle_add_guardrail(
                mock_weaviate,
                {
                    "prompt": "Test",
                    "model_name": "invalid-model",
                    "guardrails": "Test",
                },
            )

            assert len(result) == 1
            assert "Invalid model name" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_search_guardrails_success(self, mock_weaviate):
        """Test successful search_guardrails call."""
        from truthguards.core.weaviate_client import GuardrailResult

        mock_weaviate.search_guardrails.return_value = [
            GuardrailResult(
                id="id-1",
                prompt="Test",
                model_name="gpt-4",
                guardrails="Test guardrails",
                score=0.95,
            )
        ]

        from truthguards.mcp.server import handle_search_guardrails

        result = await handle_search_guardrails(
            mock_weaviate,
            {
                "prompt": "Test query",
                "model_name": "gpt-4",
                "limit": 5,
            },
        )

        assert len(result) == 1
        assert "count" in result[0].text
        assert "0.95" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_search_guardrails_no_results(self, mock_weaviate):
        """Test search_guardrails with no results."""
        mock_weaviate.search_guardrails.return_value = []

        from truthguards.mcp.server import handle_search_guardrails

        result = await handle_search_guardrails(
            mock_weaviate,
            {
                "prompt": "Unrelated query",
                "model_name": "gpt-4",
            },
        )

        assert len(result) == 1
        assert "No guardrails found" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_search_guardrails_missing_args(self, mock_weaviate):
        """Test search_guardrails with missing arguments."""
        from truthguards.mcp.server import handle_search_guardrails

        result = await handle_search_guardrails(
            mock_weaviate,
            {"prompt": "Test"},  # Missing model_name
        )

        assert len(result) == 1
        assert "Missing required arguments" in result[0].text


class TestMCPCallTool:
    """Tests for the main call_tool function."""

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        """Test calling an unknown tool."""
        mock_client = MagicMock()
        mock_client.connect.return_value = None

        with patch("truthguards.mcp.server.get_weaviate_client", return_value=mock_client):
            from truthguards.mcp.server import call_tool

            result = await call_tool("unknown_tool", {})

            assert len(result) == 1
            assert "Unknown tool" in result[0].text
