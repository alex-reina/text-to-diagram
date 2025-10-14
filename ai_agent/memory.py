"""Lightweight conversation memory tracking message history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class Message:
    """Container for chat messages."""

    role: str
    content: str

    def trimmed(self) -> "Message":
        return Message(role=self.role, content=self.content.strip())


@dataclass
class ConversationMemory:
    """Stores chat history with an optional max size."""

    max_messages: int | None = 20
    _messages: List[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        message = Message(role=role, content=content.strip())
        self._messages.append(message)
        # Enforce the retention policy immediately so every mutation stays within bounds.
        self._trim()

    def add_user_message(self, content: str) -> None:
        self.add("user", content)

    def add_ai_message(self, content: str) -> None:
        self.add("assistant", content)

    def add_system_message(self, content: str) -> None:
        self.add("system", content)

    def history(self) -> List[Message]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def _trim(self) -> None:
        if self.max_messages is None:
            return
        overflow = len(self._messages) - self.max_messages
        if overflow > 0:
            # Drop the oldest turns, preserving chronological order for the remainder.
            del self._messages[0:overflow]

    def as_langchain(self) -> List[object]:
        """Convert stored messages to LangChain message objects."""

        try:
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError(
                "langchain-core is required to build LangChain messages"
            ) from exc

        converted: List[object] = []
        for message in self._messages:
            if message.role == "assistant":
                converted.append(AIMessage(content=message.content))
            elif message.role == "user":
                converted.append(HumanMessage(content=message.content))
            elif message.role == "system":
                converted.append(SystemMessage(content=message.content))
        return converted

    def load_history(self, messages: Iterable[Message]) -> None:
        self._messages = [message.trimmed() for message in messages]
        self._trim()
