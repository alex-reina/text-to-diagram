from __future__ import annotations

from pathlib import Path

import chatbot


def test_main_runs_chat_loop_and_writes_transcript(tmp_path, monkeypatch):
    args = chatbot.parse_args([])  # baseline defaults
    transcript_path = tmp_path / "session.txt"
    args.transcript = transcript_path

    monkeypatch.setattr("chatbot.parse_args", lambda _: args)

    build_agent_calls = []
    monkeypatch.setattr(
        "chatbot.build_agent",
        lambda options: build_agent_calls.append(options) or object(),
    )
    monkeypatch.setattr("chatbot.chat_loop", lambda *a, **k: ["user: hi", "assistant: hello"])

    written = {}

    def fake_save_transcript(path: Path, transcript: list[str]) -> None:
        written["path"] = path
        written["transcript"] = transcript

    monkeypatch.setattr("chatbot.save_transcript", fake_save_transcript)

    exit_code = chatbot.main([])

    assert exit_code == 0
    assert build_agent_calls and build_agent_calls[0] is args
    assert written["path"] == transcript_path
    assert written["transcript"] == ["user: hi", "assistant: hello"]
