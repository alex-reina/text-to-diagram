# text-to-diagram

A playground for turning natural-language diagram ideas into PlantUML using a lightweight Python agent.

## Groq chat agent foundation

`chatbot.py` provides an interactive CLI that keeps short-term memory and routes the conversation through Groq's hosted models via LangChain. When responses include a `@startuml … @enduml` block, the script extracts the PlantUML code, renders a diagram automatically (saved under `diagrams/` by default), and prints both a direct image URL and an editor link that opens the same UML in PlantUML's online editor.

**Prerequisites**
- Python 3.9+
- `pip install langchain-core langchain-groq`
- On first run the CLI will prompt for your Groq API key and save it to `.env`.

**Run it**
```bash
python3 chatbot.py
```
Commands inside the chat:
- `/exit` – leave the session.
- `/reset` – clear the rolling memory window.
- `/note <text>` – push an additional system instruction into context.
- `/format <text>` – update output-format requirements mid-chat.

Pass `--memory 0` for unlimited stored turns, tweak `--model`, `--temperature`, or `--max-tokens` to suit your use case, and add `--transcript path.txt` to save the dialogue when you exit. Use `--diagram-dir rendered/` or `--diagram-format svg` to control diagram output, and the CLI will skip rendering gracefully if PlantUML or the server is unavailable.

## Streamlit front-end

Prefer a richer UI? Launch the Streamlit app:
```bash
streamlit run streamlit_app.py
```
Use the sidebar to tune the model, temperature, memory window, system instructions, output format, and diagram output type (PNG/SVG) without leaving the browser. On first launch the app requests your Groq API key and saves it to `.env`. When the assistant includes PlantUML in its reply, the app displays the raw UML alongside the rendered image plus quick links to view the image or open the encoded UML in PlantUML's online editor. Conversation history is displayed with `st.chat_message`.


## Getting an API Key

Simply register at https://console.groq.com/keys (free for now)
