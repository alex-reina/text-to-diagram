# text-to-diagram

A playground for turning natural-language diagram ideas into PlantUML using a lightweight Python agent.

## Groq chat agent foundation

`chatbot.py` provides an interactive CLI that keeps short-term memory and routes the conversation through Groq's hosted models via LangChain. When responses include a `@startuml … @enduml` block, the script extracts the PlantUML code, renders a diagram automatically (saved under `diagrams/` by default), and prints both a direct image URL and an editor link that opens the same UML in PlantUML's online editor.

**Prerequisites**
- Python 3.10+
- `pip install langchain-core langchain-groq`
- On first run the CLI will prompt for your Groq API key and save it to `.env`.

**Run it**
```bash
python3 chatbot.py
# or with the packaged console script
text-to-diagram-chat
```
Commands inside the chat:
- `/exit` – leave the session.
- `/reset` – clear the rolling memory window.
- `/note <text>` – push an additional system instruction into context.
- `/format <text>` – update output-format requirements mid-chat.

Pass `--memory 0` for unlimited stored turns, tweak `--model`, `--temperature`, or `--max-tokens` to suit your use case, and add `--transcript path.txt` to save the dialogue when you exit. Use `--diagram-dir rendered/` or `--diagram-format svg` to control diagram output, and the CLI will skip rendering gracefully if PlantUML or the server is unavailable.

The default Groq model is `llama-3.1-8b-instant`. Other tested chat-capable options include `groq/compound-mini`, `groq/compound`, `llama-3.3-70b-versatile`, `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `meta-llama/llama-4-scout-17b-16e-instruct`, `meta-llama/llama-4-maverick-17b-128e-instruct`, `moonshotai/kimi-k2-instruct`, `moonshotai/kimi-k2-instruct-0905`, `qwen/qwen3-32b`, and `allam-2-7b`.

## Streamlit front-end

Prefer a richer UI? Launch the Streamlit app:
```bash
streamlit run streamlit_app.py
# or via the console script wrapper
text-to-diagram-ui
```
Use the sidebar to tune the model, temperature, memory window, system instructions, output format, and diagram output type (PNG/SVG) without leaving the browser. On first launch the app requests your Groq API key and saves it to `.env`. When the assistant includes PlantUML in its reply, the app displays the raw UML alongside the rendered image plus quick links to view the image or open the encoded UML in PlantUML's online editor. Conversation history is displayed with `st.chat_message`.

The model picker surfaces the same set of chat-focused Groq models listed above.

## Development

Install dev dependencies and run the test suite:
```bash
python -m pip install -e .[dev]
pytest
```


## Getting an API Key

Simply register at https://console.groq.com/keys (free for now)
