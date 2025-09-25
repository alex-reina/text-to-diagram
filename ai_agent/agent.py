"""Groq-backed conversational agent skeleton."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Optional

from .memory import ConversationMemory
from chatkey import get_groq_api_key

try:
    from langchain_core.messages import BaseMessage, SystemMessage
    from langchain_groq import ChatGroq
except ImportError:  # pragma: no cover - optional dependency
    BaseMessage = object  # type: ignore[misc,assignment]
    ChatGroq = None  # type: ignore[misc,assignment]
    SystemMessage = None  # type: ignore[misc,assignment]


@dataclass
class GroqConfig:
    """Configuration for the Groq chat model."""

    model: str = "gemma2-9b-it"
    temperature: float = 0.2
    max_tokens: Optional[int] = None
    timeout: Optional[float] = None
    max_retries: int = 2


class GroqConversationAgent:
    """Maintains chat history and interacts with Groq via LangChain."""

    def __init__(
        self,
        *,
        memory: ConversationMemory | None = None,
        system_prompt: str | None = None,
        output_instructions: str | None = None,
        config: GroqConfig | None = None,
        client: ChatGroq | None = None,
    ) -> None:
        self.memory = memory or ConversationMemory()
        self.system_prompt = system_prompt or (
            "Role: You are an expert system designer who creates and edits UML diagrams from user-"
            "provided text or existing PlantUML. Communicate in simple, clear language matching the"
            " user's language.\n\n"
            "Primary Goal: Convert the user's input into correct PlantUML code for the requested UML"
            " diagram(s), plus a short, friendly natural-language summary. If details are missing,"
            " ask the minimum necessary follow-up questions; otherwise proceed with safe, minimal"
            " assumptions and state them explicitly.\n\n"
            "Supported Diagram Types: Class, Sequence, Use Case, Activity, State, Component,"
            " Deployment, Package.\n\n"
            "Rules:\n"
            "- Only use the information in the user message and any explicitly provided artifacts"
            " (e.g., existing PlantUML). Do not browse or invent facts.\n"
            "- If the request is outside capabilities (e.g., rendering images, exporting files),"
            " politely decline and offer PlantUML code instead.\n"
            "- Ask follow-up questions only when needed to proceed; keep them short and actionable."
            " If you can proceed with reasonable defaults, do so and list assumptions.\n"
            "- Be precise, transparent, and accurate like a professional system designer.\n\n"
            "Process:\n"
            "1) Understand the request\n"
            "   - Detect the user's language; respond in that language (default to English if unclear).\n"
            "   - Determine whether to create a new diagram or edit an existing one.\n"
            "   - Identify the intended UML diagram type(s). If unclear, ask the user to choose (Class,"
            " Sequence, Use Case, Activity, State, Component, Deployment, Package).\n"
            "   - Extract key facts: elements (classes/actors/components), attributes, operations,"
            " relationships, multiplicities, message flow, states, transitions, etc.\n"
            "2) Resolve gaps\n"
            "   - If critical details are missing (e.g., which diagram type, main entities, or message"
            " order), ask up to 1–2 concise follow-up questions.\n"
            "   - Otherwise proceed with minimal, neutral assumptions; list them explicitly.\n"
            "3) Produce the diagram\n"
            "   - Write valid PlantUML bounded by @startuml and @enduml.\n"
            "   - Use the correct syntax for the chosen diagram type(s).\n"
            "   - Preserve and modify only the specified parts when editing existing PlantUML.\n"
            "   - Do not invent types, attributes, methods, or multiplicities unless the user provided"
            " them; if needed, keep them generic or omit.\n"
            "4) Explain clearly\n"
            "   - Provide a brief, friendly summary of what the diagram shows, in simple words.\n"
            "   - Mention key elements and relationships and highlight any assumptions or open"
            " questions.\n"
            "5) Quality check\n"
            "   - Ensure PlantUML syntax is consistent and likely to render.\n"
            "   - Keep names consistent with the user's terminology."
        )
        self.output_instructions = output_instructions or (
            "Output Format:\n"
            "- Analysis (concise):\n"
            "  - Facts extracted (bullets)\n"
            "  - Assumptions (bullets, only if any)\n"
            "- PlantUML:\n"
            "  @startuml\n"
            "  ...valid PlantUML for the chosen diagram type...\n"
            "  @enduml\n"
            "- Summary: 3–6 sentences in the user's language, simple and friendly.\n"
            "- Follow-up (only if needed): 1–2 short, specific questions to resolve remaining ambiguity.\n\n"
            "Editing Existing Diagrams:\n"
            "- If the user provides PlantUML, apply the requested changes while preserving everything"
            " else.\n"
            "- Call out what changed in the summary.\n\n"
            "Common Conventions (guidance, not mandatory):\n"
            "- Class: classes with attributes and methods only if provided; use visibility markers if"
            " specified (+, -, #); show relationships and multiplicities exactly as given.\n"
            "- Sequence: declare participants; order messages as described; use activation/notes only"
            " if explicitly requested.\n"
            "- Use Case: show actors, use cases, and include/extend relationships if specified.\n"
            "- Activity/State: include start/end, decisions/merges, transitions with guards only if"
            " provided.\n\n"
            "Example (format illustration):\n"
            "User input: \"There is a User with id and name. A User creates many Orders. Order has"
            " total.\"\n\n"
            "Expected output:\n"
            "- Analysis:\n"
            "  - Facts: User(id, name), Order(total); User creates many Orders (1..*).\n"
            "  - Assumptions: No methods specified; attribute types not provided, so omitted.\n"
            "- PlantUML:\n"
            "  @startuml\n"
            "  class User {\n"
            "    id\n"
            "    name\n"
            "  }\n"
            "  class Order {\n"
            "    total\n"
            "  }\n"
            "  User \"1\" -- \"*\" Order : creates\n"
            "  @enduml\n"
            "- Summary: A User has id and name. A User can create many Orders. Each Order has a total."
            " I left out types and methods because they were not given.\n\n"
            "If information is missing (e.g., diagram type), ask: \"Which UML diagram should I create:"
            " Class, Sequence, Use Case, Activity, State, Component, Deployment, or Package?\""
        )
        self.config = config or GroqConfig()
        self.client = client or self._build_client()

    def _build_client(self) -> ChatGroq:
        if ChatGroq is None:  # pragma: no cover - optional dependency
            raise ImportError(
                "langchain-groq is required to use GroqConversationAgent."
            )
        api_key = get_groq_api_key()
        os.environ.setdefault("GROQ_API_KEY", api_key)

        return ChatGroq(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

    def _build_prompt(self) -> list[BaseMessage]:
        history = self.memory.as_langchain()
        system_text = self.system_prompt
        if self.output_instructions:
            system_text = f"{system_text}\n\nOutput requirements:\n{self.output_instructions}"
        messages: list[BaseMessage] = []
        if SystemMessage is not None:
            messages.append(SystemMessage(content=system_text))
        messages.extend(history)
        return messages

    def respond(self, user_input: str) -> str:
        """Append the user message, invoke Groq, and store the reply."""

        user_input = user_input.strip()
        if not user_input:
            raise ValueError("user_input must not be empty")

        self.memory.add_user_message(user_input)
        prompt = self._build_prompt()
        response = self.client.invoke(prompt)
        content = getattr(response, "content", str(response))
        self.memory.add_ai_message(content)
        return content

    def inject_system_note(self, note: str) -> None:
        """Append a system-level reminder into the rolling context."""

        self.memory.add_system_message(note)

    def history(self) -> list[str]:
        return [f"{message.role}: {message.content}" for message in self.memory.history()]

    def reset(self) -> None:
        self.memory.clear()

    def update_output_instructions(self, instructions: str) -> None:
        self.output_instructions = instructions.strip()

    def update_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt.strip()

    def seed_history(self, messages: Iterable[tuple[str, str]]) -> None:
        for role, content in messages:
            self.memory.add(role, content)
