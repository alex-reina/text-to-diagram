"""Interactive CLI for the Groq-backed chat agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from ai_agent import (
    ConversationMemory,
    GroqConfig,
    GroqConversationAgent,
    PlantUMLRenderingError,
    render_plantuml_from_text,
    save_diagrams,
    DEFAULT_GROQ_MODEL,
    GROQ_TEXT_MODELS,
)
from chatkey import ensure_api_key


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with a Groq model that remembers recent context.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_GROQ_MODEL,
        help=f"Groq chat model to use (common choices: {', '.join(GROQ_TEXT_MODELS)}).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the model.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Optional cap on generated tokens.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Retry attempts for Groq API calls.",
    )
    parser.add_argument(
        "--memory",
        type=int,
        default=20,
        help="How many recent messages to retain in memory (set 0 for unlimited).",
    )
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Custom system prompt for the agent persona.",
    )
    parser.add_argument(
        "--output-format",
        default=None,
        help="Extra instructions describing the desired output style.",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=None,
        help="Inject additional system notes before the chat (repeatable).",
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        default=None,
        help="Optional path to save the conversation transcript when exiting.",
    )
    parser.add_argument(
        "--diagram-dir",
        type=Path,
        default=Path("diagrams"),
        help="Directory where generated PlantUML diagrams are written.",
    )
    parser.add_argument(
        "--diagram-format",
        choices=("png", "svg"),
        default="png",
        help="Image format to request from the PlantUML server.",
    )
    return parser.parse_args(argv)


def build_agent(args: argparse.Namespace) -> GroqConversationAgent:
    memory_size = None if args.memory == 0 else args.memory
    memory = ConversationMemory(max_messages=memory_size)
    config = GroqConfig(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        max_retries=args.max_retries,
    )
    agent = GroqConversationAgent(
        memory=memory,
        system_prompt=args.system_prompt,
        output_instructions=args.output_format,
        config=config,
    )
    if args.note:
        for note in args.note:
            if note:
                agent.inject_system_note(note)
    return agent


def chat_loop(agent: GroqConversationAgent, *, diagram_dir: Path, diagram_format: str) -> list[str]:
    print("Type '/exit' to leave, '/reset' to clear memory, '/note <text>' to add a system note,")
    print("or '/format <text>' to update output instructions on the fly.")

    transcript: list[str] = []
    while True:
        try:
            user_input = input("You > ")
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break
        command = user_input.strip()
        # Interpret lightweight slash commands before sending text to the model.
        if command.lower() in {"/exit", "exit", "quit"}:
            print("Goodbye!")
            break
        if command.startswith("/reset"):
            agent.reset()
            transcript.append("# reset")
            print("Memory cleared.")
            continue
        if command.startswith("/note "):
            note = command[len("/note ") :].strip()
            if note:
                agent.inject_system_note(note)
                transcript.append(f"system-note: {note}")
                print("Added system note.")
            continue
        if command.startswith("/format "):
            fmt = command[len("/format ") :].strip()
            agent.update_output_instructions(fmt)
            transcript.append(f"output-format: {fmt}")
            print("Updated output instructions.")
            continue
        if not command:
            continue

        try:
            response = agent.respond(command)
        except Exception as exc:  # noqa: BLE001
            print(f"Error: {exc}")
            break

        transcript.append(f"user: {command}")
        transcript.append(f"assistant: {response}")
        print(f"Agent > {response}")

        try:
            diagrams = render_plantuml_from_text(response, fmt=diagram_format)
        except (ImportError, PlantUMLRenderingError) as exc:
            print(f"Diagram rendering skipped: {exc}", file=sys.stderr)
            diagrams = []

        for diagram in diagrams:
            # Surface links immediately so CLI users can open results without waiting for saves.
            if diagram.image_url:
                print(f"Diagram image URL: {diagram.image_url}")
                transcript.append(f"diagram_image_url: {diagram.image_url}")
            if diagram.editor_url:
                print(f"Diagram editor URL: {diagram.editor_url}")
                transcript.append(f"diagram_editor_url: {diagram.editor_url}")

        if diagrams:
            try:
                paths = save_diagrams(diagrams, diagram_dir)
            except Exception as exc:  # noqa: BLE001
                print(f"Failed to save diagrams: {exc}", file=sys.stderr)
            else:
                for diagram, path in zip(diagrams, paths, strict=False):
                    print(f"Diagram saved to {path}")
                    transcript.append(f"diagram: {path}")
    return transcript


def save_transcript(path: Path, transcript: list[str]) -> None:
    if not transcript:
        return
    path.write_text("\n".join(transcript) + "\n", encoding="utf-8")
    print(f"Transcript written to {path}")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit:
        # argparse already printed help/error
        return 2

    try:
        ensure_api_key()
        agent = build_agent(args)
    except ImportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    transcript = chat_loop(agent, diagram_dir=args.diagram_dir, diagram_format=args.diagram_format)
    if args.transcript:
        try:
            save_transcript(args.transcript, transcript)
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to write transcript: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
