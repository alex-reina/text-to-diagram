from __future__ import annotations

from ai_agent.plantuml_utils import extract_plantuml_blocks, render_plantuml_from_text


def test_extract_plantuml_blocks_finds_multiple_snippets():
    text = """
    Analysis:
    - placeholder

    @startuml
    Alice -> Bob : Hello
    @enduml

    Notes between diagrams.

    @startuml
    Bob -> Carol : Hi!
    @enduml
    """

    blocks = extract_plantuml_blocks(text)

    assert len(blocks) == 2
    assert blocks[0].startswith("@startuml")
    assert blocks[0].endswith("@enduml")
    assert "Alice -> Bob" in blocks[0]
    assert "Bob -> Carol" in blocks[1]


def test_render_plantuml_from_text_passes_snippets_through(mocker):
    fake_diagram = object()
    render = mocker.patch("ai_agent.plantuml_utils.render_plantuml", return_value=fake_diagram)
    text = "@startuml\nAlice -> Bob : Hi\n@enduml"

    diagrams = render_plantuml_from_text(text, fmt="svg")

    assert diagrams == [fake_diagram]
    render.assert_called_once()
    args, kwargs = render.call_args
    assert args[0].startswith("@startuml")
    assert kwargs["fmt"] == "svg"
