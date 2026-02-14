"""MCP server for TruthGuards."""

import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from truthguards.core.config import get_settings
from truthguards.core.weaviate_client import WeaviateClient, get_weaviate_client

# Create MCP server
server = Server("truthguards")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    settings = get_settings()
    models_description = ", ".join(settings.models) if settings.models else "any model name"

    return [
        Tool(
            name="add_guardrail",
            description="Add a new guardrail to the TruthGuards database. Guardrails are textual instructions that help prevent LLM hallucinations for specific types of prompts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt pattern or question type this guardrail applies to",
                    },
                    "model_name": {
                        "type": "string",
                        "description": f"The LLM model this guardrail is for. Available models: {models_description}",
                    },
                    "guardrails": {
                        "type": "string",
                        "description": "The guardrail text to add to prompts matching this pattern",
                    },
                },
                "required": ["prompt", "model_name", "guardrails"],
            },
        ),
        Tool(
            name="search_guardrails",
            description="Search for relevant guardrails using hybrid search (keyword + semantic). Returns guardrails that are most relevant to the given prompt and model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to search for relevant guardrails",
                    },
                    "model_name": {
                        "type": "string",
                        "description": f"Filter results by LLM model. Available models: {models_description}",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of guardrails to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["prompt", "model_name"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    client = get_weaviate_client()

    # Ensure client is connected
    try:
        client.connect()
    except Exception as e:
        return [TextContent(type="text", text=f"Error connecting to Weaviate: {str(e)}")]

    if name == "add_guardrail":
        return await handle_add_guardrail(client, arguments)
    elif name == "search_guardrails":
        return await handle_search_guardrails(client, arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def handle_add_guardrail(
    client: WeaviateClient, arguments: dict[str, Any]
) -> list[TextContent]:
    """Handle the add_guardrail tool call."""
    prompt = arguments.get("prompt")
    model_name = arguments.get("model_name")
    guardrails = arguments.get("guardrails")

    if not all([prompt, model_name, guardrails]):
        return [TextContent(type="text", text="Missing required arguments: prompt, model_name, guardrails")]

    # Validate model name
    settings = get_settings()
    if settings.models and model_name not in settings.models:
        return [
            TextContent(
                type="text",
                text=f"Invalid model name '{model_name}'. Available models: {', '.join(settings.models)}",
            )
        ]

    try:
        guardrail_id = client.add_guardrail(
            prompt=prompt,
            model_name=model_name,
            guardrails=guardrails,
        )
        return [
            TextContent(
                type="text",
                text=f"Successfully created guardrail with ID: {guardrail_id}",
            )
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating guardrail: {str(e)}")]


async def handle_search_guardrails(
    client: WeaviateClient, arguments: dict[str, Any]
) -> list[TextContent]:
    """Handle the search_guardrails tool call."""
    prompt = arguments.get("prompt")
    model_name = arguments.get("model_name")
    limit = arguments.get("limit", 5)

    if not prompt or not model_name:
        return [TextContent(type="text", text="Missing required arguments: prompt, model_name")]

    try:
        results = client.search_guardrails(
            prompt=prompt,
            model_name=model_name,
            limit=limit,
        )

        if not results:
            return [
                TextContent(
                    type="text",
                    text=f"No guardrails found for model '{model_name}' matching the given prompt.",
                )
            ]

        # Format results
        formatted_results = []
        for i, r in enumerate(results, 1):
            formatted_results.append(
                {
                    "rank": i,
                    "score": round(r.score, 4),
                    "guardrails": r.guardrails,
                    "original_prompt": r.prompt,
                }
            )

        output = {
            "count": len(results),
            "model": model_name,
            "results": formatted_results,
        }

        return [TextContent(type="text", text=json.dumps(output, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error searching guardrails: {str(e)}")]


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point for the MCP server."""
    import asyncio

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
