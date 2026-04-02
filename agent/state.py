"""
LangGraph state schema for the Codebase Onboarding Agent.

Every node receives this state and returns a *partial* dict with only
the keys it wants to update.  LangGraph merges the updates automatically.
"""
from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    # ── inputs (set once at invocation) ──────────────────────────────────
    repo_url: str
    repo_name: str
    api_key: str            # OpenRouter API key (passed via state so nodes can use it)

    # ── intermediate results ─────────────────────────────────────────────
    repo_path: str           # local path to the cloned repo
    structure: str           # human-readable file tree
    key_files_content: str   # actual text of key config/entry files
    code_info: str           # tree-sitter extracted info summary
    tech_stack: dict         # parsed JSON from LLM
    entry_points: str        # markdown from LLM
    module_summaries: str    # markdown from LLM
    data_flow: str           # markdown from LLM
    caveats: str             # markdown from LLM (formerly "gotchas")

    # ── computed metrics ─────────────────────────────────────────────────
    metrics: dict            # {total_files, languages, loc, dependencies}

    # ── final output ─────────────────────────────────────────────────────
    report: str              # full compiled onboarding report

    # ── status ───────────────────────────────────────────────────────────
    error: str               # non-empty when something goes wrong
