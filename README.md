# 🕵️‍♂️ Codebase Onboarding Agent

A premium, LangGraph-powered GitHub repository analysis tool designed to generate senior-developer onboarding reports instantly. Built completely with modern async Python, Streamlit, ChromaDB, and Google's Gemini 2.0 Flash context modeling.

## ✨ Features

- 🧠 **LangGraph Orchestration**: Employs a robust, Directed Acyclic Graph (DAG) state machine to break down unknown codebases logically.
- 🌳 **Tree-sitter Parsing**: Lazily loads and parses structure via ASTs for `Python`, `JavaScript`, and `TypeScript`.
- 🔍 **Semantic Search Engine**: Incorporates `ChromaDB` offline vector store and Gemini embeddings for lightning-fast codebase search.
- 💅 **Custom UI Architecture**: A deeply integrated FastAPI backend serving a gorgeous, dark-mode Tailwind CSS Single Page Application via WebSockets.
- 🤖 **Gemini 2.0 Native**: Skips heavy LangChain wrappers and integrates directly with the `google-generativeai` SDK.

## 🚀 Getting Started

Ensure you have Python 3.10+ installed and a valid Gemini API key.

1. **Clone the Repo**
```bash
git clone https://github.com/KindaJayant/codebase-onboarding-agent.git
cd codebase-onboarding-agent
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Variables**
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

4. **Launch Application**
```bash
uvicorn main:app --reload
```
Open up **`http://localhost:8000`** in your browser, punch in a Github repository link, and let the agent get to work!

## 📂 Project Structure

- `main.py`: Contains the FastAPI server, WebSocket endpoints, and REST routes.
- `static/`: Contains the Tailwind CSS compiled files, `index.html`, and Vanilla JS application logic.
- `agent/`: LangGraph logic (`nodes.py`, `graph.py`, `state.py`, `prompts.py`).
- `utils/`: Utilities for cloning (`repo.py`), code ast (`parser.py`), and semantic indexing (`vectorstore.py`).
- `db/`: Locally instantiated ChromaDB index directory.

## 🛡️ License

MIT License. See [LICENSE](LICENSE) for details.
