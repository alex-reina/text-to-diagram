"""Streamlit interface for the Groq-backed diagram agent."""

from __future__ import annotations

import os
from typing import List

import streamlit as st

from ai_agent import (
    ConversationMemory,
    GroqConfig,
    GroqConversationAgent,
    PlantUMLRenderingError,
    PlantUMLDiagram,
    render_plantuml_from_text,
)
from chatkey import ensure_api_key


def build_agent(
    *,
    model: str,
    temperature: float,
    max_tokens: int | None,
    memory_limit: int | None,
    system_prompt: str | None,
    output_format: str | None,
) -> GroqConversationAgent:
    memory = ConversationMemory(max_messages=memory_limit)
    config = GroqConfig(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    agent = GroqConversationAgent(
        memory=memory,
        system_prompt=system_prompt,
        output_instructions=output_format,
        config=config,
    )
    return agent


def agent_from_state(settings: dict[str, object]) -> GroqConversationAgent:
    key = tuple(settings.items())
    if st.session_state.get("agent_key") != key:
        st.session_state.agent = build_agent(
            model=settings["model"],
            temperature=settings["temperature"],
            max_tokens=settings["max_tokens"],
            memory_limit=settings["memory_limit"],
            system_prompt=settings["system_prompt"],
            output_format=settings["output_format"],
        )
        st.session_state.agent_key = key
        st.session_state["diagram_records"] = []
    return st.session_state.agent


def display_diagram(diagram: PlantUMLDiagram, *, show_code: bool) -> None:
    if show_code:
        st.code(diagram.code, language="text")
    st.image(diagram.data, caption=f"Generated diagram ({diagram.format})")

    links: List[str] = []
    if diagram.image_url:
        links.append(f"[View image]({diagram.image_url})")
    if diagram.editor_url:
        links.append(f"[Open in PlantUML editor]({diagram.editor_url})")
    if links:
        st.markdown(" · ".join(links))


def display_history(agent: GroqConversationAgent) -> None:
    diagram_records = st.session_state.setdefault("diagram_records", [])
    for index, message in enumerate(agent.memory.history()):
        role = message.role
        content = message.content
        if role not in {"user", "assistant", "system"}:
            role = "assistant"
        with st.chat_message(role):
            st.markdown(content)
            if role == "assistant":
                for record in diagram_records:
                    if record.get("message_index") != index:
                        continue
                    diagram = record.get("diagram")
                    if diagram is None:
                        continue
                    show_code = diagram.code not in content
                    display_diagram(diagram, show_code=show_code)


def main() -> None:
    st.set_page_config(page_title="My Diagram Agent", layout="wide")
    st.title("My Diagram Agent")
    st.caption("Chat with a Groq model that remembers context and crafts PlantUML output.")

    if "groq_key_loaded" not in st.session_state:
        key = ensure_api_key()
        if not key:
            st.stop()
        st.session_state.groq_key_loaded = True

    with st.sidebar:
        st.header("Session Settings")
        model = st.selectbox(
            "Groq model",
            options=["gemma2-9b-it", "mixtral-8x7b-32768", "llama3-70b-8192"],
            index=0,
        )
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
        max_tokens = st.number_input(
            "Max tokens (0 = default)",
            min_value=0,
            value=0,
            step=50,
            help="Limit the size of responses. Leave at 0 to use the model default.",
        )
        memory_limit_val = st.number_input(
            "Memory window (0 = unlimited)",
            min_value=0,
            value=30,
            step=5,
            help="Number of recent messages to keep in context.",
        )
        memory_limit = None if memory_limit_val == 0 else int(memory_limit_val)

        system_prompt = st.text_area(
            "System prompt",
            value=(
                "Role: You are an expert system designer who creates and edits UML diagrams from"
                " user-provided text or existing PlantUML. Communicate in simple, clear language"
                " matching the user's language."
            ),
            height=120,
        )
        output_format = st.text_area(
            "Output instructions",
            value=(
                "Output Format:\n"
                "- Analysis (concise):\n"
                "  - Facts extracted (bullets)\n"
                "  - Assumptions (bullets, only if any)\n"
                "- PlantUML:\n"
                "  @startuml\n"
                "  ...valid PlantUML for the chosen diagram type...\n"
                "  @enduml\n"
                "- Summary: 3–6 sentences in the user's language, simple and friendly.\n"
                "- Follow-up (only if needed): 1–2 short, specific questions to resolve remaining ambiguity."
            ),
            height=160,
        )
        diagram_format = st.selectbox(
            "Diagram format",
            options=("png", "svg"),
            index=0,
        )
        if st.button("Reset conversation", use_container_width=True):
            st.session_state.pop("agent", None)
            st.session_state.pop("agent_key", None)
            st.session_state.pop("diagram_records", None)
            st.rerun()

    settings = {
        "model": model,
        "temperature": temperature,
        "max_tokens": None if max_tokens == 0 else int(max_tokens),
        "memory_limit": memory_limit,
        "system_prompt": system_prompt.strip() or None,
        "output_format": output_format.strip() or None,
    }

    agent = agent_from_state(settings)
    display_history(agent)

    prompt = st.chat_input("Describe the diagram you need...")
    if prompt:
        try:
            response = agent.respond(prompt)
        except Exception as exc:  # pragma: no cover - network/API errors
            st.error(f"Failed to contact Groq: {exc}")
        else:
            try:
                diagrams = render_plantuml_from_text(response, fmt=diagram_format)
            except ImportError as exc:
                st.warning(f"Install plantuml to render diagrams automatically: {exc}")
                diagrams = []
            except PlantUMLRenderingError as exc:
                st.warning(f"PlantUML rendering failed: {exc}")
                diagrams = []
            if diagrams:
                records = st.session_state.setdefault("diagram_records", [])
                message_index = len(agent.memory.history()) - 1
                for diagram in diagrams:
                    if not any(
                        record.get("message_index") == message_index
                        and record.get("diagram")
                        and record["diagram"].code == diagram.code
                        for record in records
                    ):
                        records.append(
                            {
                                "message_index": message_index,
                                "diagram": diagram,
                            }
                        )
            st.rerun()


if __name__ == "__main__":
    main()
