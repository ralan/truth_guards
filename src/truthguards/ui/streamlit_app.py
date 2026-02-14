"""Streamlit web interface for TruthGuards."""

import os

import httpx
import streamlit as st

# API base URL - can be configured via environment variable
API_BASE_URL = os.environ.get("TRUTHGUARDS_API_URL", "http://localhost:8000")


def get_models() -> list[str]:
    """Fetch available models from the API."""
    try:
        response = httpx.get(f"{API_BASE_URL}/models", timeout=5.0)
        response.raise_for_status()
        return response.json().get("models", [])
    except Exception:
        # Fallback to default models if API is not available
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
        ]


def add_guardrail(prompt: str, model_name: str, guardrails: str) -> dict:
    """Add a guardrail via the API."""
    response = httpx.post(
        f"{API_BASE_URL}/guardrails",
        json={
            "prompt": prompt,
            "model_name": model_name,
            "guardrails": guardrails,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()


def search_guardrails(prompt: str, model_name: str, limit: int = 5) -> dict:
    """Search for guardrails via the API."""
    response = httpx.post(
        f"{API_BASE_URL}/guardrails/search",
        json={
            "prompt": prompt,
            "model_name": model_name,
            "limit": limit,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="TruthGuards",
        page_icon="shield",
        layout="wide",
    )

    st.title("TruthGuards")
    st.markdown(
        """
        **RAG-based guardrail retrieval system for AI agents.**

        Store and retrieve relevant guardrails to prevent LLM hallucinations.
        """
    )

    # Fetch available models
    models = get_models()

    # Create tabs
    tab_add, tab_search = st.tabs(["Add Guardrail", "Search Guardrails"])

    # Add Guardrail Tab
    with tab_add:
        st.header("Add New Guardrail")
        st.markdown(
            "Add a guardrail that will be retrieved when similar prompts are processed."
        )

        with st.form("add_guardrail_form"):
            add_prompt = st.text_area(
                "Prompt Pattern",
                placeholder="Enter the type of prompt or question this guardrail applies to...",
                help="Describe the kind of prompt this guardrail should be applied to",
                height=100,
            )

            add_model = st.selectbox(
                "LLM Model",
                options=models,
                help="Select the model this guardrail is designed for",
            )

            add_guardrails = st.text_area(
                "Guardrail Text",
                placeholder="Enter the guardrail instructions to add to matching prompts...",
                help="The text that will be added to prompts to prevent hallucinations",
                height=150,
            )

            submitted = st.form_submit_button("Add Guardrail", type="primary")

            if submitted:
                if not add_prompt or not add_guardrails:
                    st.error("Please fill in both the prompt pattern and guardrail text.")
                else:
                    try:
                        result = add_guardrail(add_prompt, add_model, add_guardrails)
                        st.success(f"Guardrail created successfully! ID: {result['id']}")
                    except httpx.HTTPStatusError as e:
                        st.error(f"Failed to create guardrail: {e.response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Search Guardrails Tab
    with tab_search:
        st.header("Search Guardrails")
        st.markdown(
            "Find relevant guardrails for a given prompt using hybrid search."
        )

        with st.form("search_guardrails_form"):
            search_prompt = st.text_area(
                "Prompt",
                placeholder="Enter the prompt you want to find guardrails for...",
                help="The prompt to search for relevant guardrails",
                height=100,
            )

            col1, col2 = st.columns([2, 1])
            with col1:
                search_model = st.selectbox(
                    "LLM Model",
                    options=models,
                    help="Filter results by model",
                    key="search_model",
                )
            with col2:
                search_limit = st.number_input(
                    "Max Results",
                    min_value=1,
                    max_value=50,
                    value=5,
                    help="Maximum number of guardrails to return",
                )

            search_submitted = st.form_submit_button("Search", type="primary")

        if search_submitted:
            if not search_prompt:
                st.error("Please enter a prompt to search for.")
            else:
                try:
                    with st.spinner("Searching..."):
                        results = search_guardrails(
                            search_prompt, search_model, search_limit
                        )

                    if results["count"] == 0:
                        st.info(
                            f"No guardrails found for model '{search_model}' matching your prompt."
                        )
                    else:
                        st.success(f"Found {results['count']} guardrail(s)")

                        for i, guardrail in enumerate(results["results"], 1):
                            with st.expander(
                                f"**{i}. Score: {guardrail['score']:.4f}**",
                                expanded=(i == 1),
                            ):
                                st.markdown("**Original Prompt Pattern:**")
                                st.text(guardrail["prompt"])

                                st.markdown("**Guardrail Text:**")
                                st.markdown(
                                    f"```\n{guardrail['guardrails']}\n```"
                                )

                                st.caption(f"ID: {guardrail['id']}")

                except httpx.HTTPStatusError as e:
                    st.error(f"Search failed: {e.response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Sidebar with info
    with st.sidebar:
        st.header("About")
        st.markdown(
            """
            **TruthGuards** helps AI agents retrieve relevant guardrails
            to prevent hallucinations.

            **How it works:**
            1. Store guardrails with associated prompt patterns
            2. When processing a prompt, search for relevant guardrails
            3. Add retrieved guardrails to your system prompt

            **Hybrid Search:**
            Combines keyword matching (BM25) with semantic similarity
            for best results.
            """
        )

        st.divider()

        # Health check
        st.header("Status")
        try:
            response = httpx.get(f"{API_BASE_URL}/health", timeout=2.0)
            health = response.json()
            if health.get("weaviate_connected"):
                st.success("API: Connected")
                st.success("Weaviate: Connected")
            else:
                st.warning("API: Connected")
                st.error("Weaviate: Disconnected")
        except Exception:
            st.error("API: Disconnected")


if __name__ == "__main__":
    main()
