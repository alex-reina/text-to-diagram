from __future__ import annotations

from pathlib import Path

from ai_agent import streamlit_launcher


def test_streamlit_launcher_invokes_streamlit_cli(tmp_path, monkeypatch):
    called = {}

    def fake_call(cmd):
        called["cmd"] = cmd
        return 0

    monkeypatch.setattr(streamlit_launcher.subprocess, "call", fake_call)

    exit_code = streamlit_launcher.main(["--server.headless", "true"])

    expected = Path(streamlit_launcher.__file__).resolve().parent.parent / "streamlit_app.py"
    assert exit_code == 0
    assert called["cmd"][:3] == ["streamlit", "run", str(expected)]
    assert called["cmd"][3:] == ["--server.headless", "true"]


def test_streamlit_launcher_handles_keyboard_interrupt(monkeypatch):
    def interrupting_call(cmd):
        raise KeyboardInterrupt

    monkeypatch.setattr(streamlit_launcher.subprocess, "call", interrupting_call)

    exit_code = streamlit_launcher.main([])

    assert exit_code == 130
