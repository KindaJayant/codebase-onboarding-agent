# 🕵️‍♂️ Codebase Onboarding Agent

![Hero Image](static/assets/hero.png)

> **Unlock the secrets of any codebase in seconds.** The Codebase Onboarding Agent is a high-fidelity, autonomous intelligence engine designed to transform massive, complex GitHub repositories into structured, senior-developer-level onboarding reports.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-2D3748?style=for-the-badge&logo=langchain)](https://langchain-ai.github.io/langgraph/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Qwen_3.6-6929F4?style=for-the-badge)](https://openrouter.ai/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-522D80?style=for-the-badge)](https://www.trychroma.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

---

## ✨ Key Features

- 🧠 **Autonomous DAG Orchestration**: Powered by **LangGraph**, the agent executes a sophisticated, multi-stage Directed Acyclic Graph (DAG) to decompose codebases logicallly.
- 🌳 **Polyglot AST Extraction**: Utilizes **Tree-sitter** for lazy-loading and deep structural analysis of `Python`, `JavaScript`, and `TypeScript`.
- 🔍 **Local Semantic Memory**: Implements **ChromaDB** with **local ONNX-backed embeddings** (`all-MiniLM-L6-v2`) for instant, private, and free semantic code search.
- ⚡ **Real-time Pipeline Streaming**: A modern **FastAPI** backend streams live analysis progress directly to the UI via **WebSockets**.
- 💅 **High-Fidelity Dashboard**: A gorgeous, dark-mode SPA built with **Tailwind CSS**, featuring dynamic metrics, interactive module maps, and architecture visualizations.
- 🤖 **Infinite Context via OpenRouter**: Seamlessly routes through 100+ models, currently optimized for **Qwen 3.6 Plus Preview** to handle enterprise-scale repositories.

---

## 🏗️ System Architecture

The agent operates through a strictly ordered execution pipeline, ensuring information scales from raw structural data to high-level architectural insights.

```mermaid
graph TD
    A[User Inputs GitHub URL] -->|WebSocket| B(FastAPI Server)
    B --> C{LangGraph Workflow}
    
    subgraph "Agent DAG Sequence"
    C --> D[parse_structure]
    D --> E[identify_tech_stack]
    E --> F[find_entry_points]
    F --> G[summarize_modules]
    G --> H[trace_data_flow]
    H --> I[extract_caveats]
    I --> J[compile_report]
    end
    
    J -->|JSON State| K[Tailwind Dashboard]
    D -.->|Sync| L[(ChromaDB Vector Store)]
    L -.->|REST| M[/api/search]
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (Required for LangGraph and Async FastAPI)
- **Node.js / NPM** (Required for Tailwind CSS compilation)
- **Git** (Installed on system PATH)

### 1. Installation
```bash
git clone https://github.com/KindaJayant/codebase-onboarding-agent.git
cd codebase-onboarding-agent
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
# Get yours at https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Build Styles & Launch
```bash
# Build Tailwind CSS (v3)
npx tailwindcss -i ./static/input.css -o ./static/output.css

# Launch the Backend Engine
uvicorn main:app --reload
```

Visit **`http://localhost:8000`** and begin your first analysis.

---

## 📂 Project Structure

- `main.py`: The central FastAPI gateway handling HTTP, WebSockets, and environment orchestration.
- `agent/`:
    - `graph.py`: Defines the LangGraph topology and state logic.
    - `nodes.py`: The implementation layer for each LLM-backed analysis stage.
    - `prompts.py`: Highly-tuned system instructions for senior developer personas.
- `utils/`:
    - `repo.py`: Robust Git management and local OS temp buffering logic.
    - `parser.py`: Multi-language Tree-sitter AST extraction utilities.
    - `vectorstore.py`: Local ChromaDB indexing and ONNX embedding logic.
- `static/`: The Vanilla JavaScript SPA, including Tailwind source and compiled outputs.
- `db/`: Locally persistent vector index directory.

---

## 🛠️ Technical Deep Dive

### Embedding Strategy
By default, this agent uses **`all-MiniLM-L6-v2`** via the `chromadb` default embedding function. This runs completely on your CPU, ensuring that your codebase structure is never sent to a cloud embedding API, preserving your privacy and OpenRouter quotas.

### Rate Limit Resilience
The `nodes.py` engine features an **Exponential Backoff** retry loop. If OpenRouter's free-tier proxies hit a 429 Rate Limit, the agent will gracefully pause for 15 seconds and automatically resume, preventing UI crashes.

---

## 🛡️ License

MIT License. See [LICENSE](LICENSE) for details. Developed with ❤️ for the global open-source community.
