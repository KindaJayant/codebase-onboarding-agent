"""
LangGraph node functions.

Each node:
  • receives the full AgentState
  • returns a **partial dict** of only the keys it updates
  • never mutates the incoming state in-place
"""
import json
import os
import traceback

from google import generativeai as genai

from . import prompts
from utils import repo as repo_utils
from utils import parser as parser_utils


# ── helpers ──────────────────────────────────────────────────────────────────

def _call_gemini(api_key: str, prompt: str) -> str:
    """Send a single prompt to Gemini 2.0 Flash and return the text response."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction from LLM output."""
    # Strip markdown code fences if present
    if '```json' in text:
        text = text.split('```json', 1)[1].split('```', 1)[0]
    elif '```' in text:
        text = text.split('```', 1)[1].split('```', 1)[0]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _collect_code_info(repo_path: str) -> str:
    """Run tree-sitter over the repo and return a summarised string."""
    summaries = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in repo_utils.EXCLUDE_DIRS]
        for fname in files:
            _, ext = os.path.splitext(fname)
            if ext not in ('.py', '.js', '.jsx', '.ts', '.tsx'):
                continue
            fpath = os.path.join(root, fname)
            info = parser_utils.extract_code_info(fpath)
            if info is None:
                continue
            rel = os.path.relpath(fpath, repo_path)
            parts = []
            if info['classes']:
                parts.append(f"  classes: {', '.join(info['classes'])}")
            if info['functions']:
                parts.append(f"  functions: {', '.join(info['functions'][:20])}")
            if info['imports']:
                parts.append(f"  imports: {', '.join(info['imports'][:10])}")
            if parts:
                summaries.append(f"📄 {rel}\n" + "\n".join(parts))
    return "\n\n".join(summaries) if summaries else "(tree-sitter analysis unavailable)"


# ── nodes ────────────────────────────────────────────────────────────────────

def parse_structure(state: dict) -> dict:
    """Clone the repo, generate the file tree, read key files, run tree-sitter."""
    try:
        repo_name = state['repo_name']
        repo_url = state['repo_url']
        repo_path = os.path.abspath(os.path.join('./temp', repo_name))

        repo_utils.clone_repo(repo_url, repo_path)

        structure = repo_utils.get_file_tree(repo_path)
        key_files_content = repo_utils.read_key_files(repo_path)
        code_info = _collect_code_info(repo_path)

        return {
            'repo_path': repo_path,
            'structure': structure,
            'key_files_content': key_files_content,
            'code_info': code_info,
        }
    except Exception as e:
        return {'error': f"Clone/parse failed: {e}\n{traceback.format_exc()}"}


def identify_tech_stack(state: dict) -> dict:
    """Ask Gemini to identify the tech stack and return parsed JSON."""
    if state.get('error'):
        return {}
    prompt = prompts.TECH_STACK_PROMPT.format(
        structure=state['structure'],
        key_files_content=state['key_files_content'],
    )
    raw = _call_gemini(state['api_key'], prompt)
    return {'tech_stack': _extract_json(raw)}


def find_entry_points(state: dict) -> dict:
    if state.get('error'):
        return {}
    prompt = prompts.ENTRY_POINTS_PROMPT.format(
        structure=state['structure'],
        key_files_content=state['key_files_content'],
        code_info=state.get('code_info', ''),
    )
    return {'entry_points': _call_gemini(state['api_key'], prompt)}


def summarize_modules(state: dict) -> dict:
    if state.get('error'):
        return {}
    prompt = prompts.MODULE_SUMMARIES_PROMPT.format(
        structure=state['structure'],
        key_files_content=state['key_files_content'],
    )
    return {'module_summaries': _call_gemini(state['api_key'], prompt)}


def trace_data_flow(state: dict) -> dict:
    if state.get('error'):
        return {}
    prompt = prompts.DATA_FLOW_PROMPT.format(
        tech_stack=json.dumps(state.get('tech_stack', {}), indent=2),
        entry_points=state.get('entry_points', ''),
        module_summaries=state.get('module_summaries', ''),
        structure=state['structure'],
    )
    return {'data_flow': _call_gemini(state['api_key'], prompt)}


def extract_gotchas(state: dict) -> dict:
    if state.get('error'):
        return {}
    prompt = prompts.GOTCHAS_PROMPT.format(
        structure=state['structure'],
        tech_stack=json.dumps(state.get('tech_stack', {}), indent=2),
        key_files_content=state['key_files_content'],
    )
    return {'gotchas': _call_gemini(state['api_key'], prompt)}


def compile_report(state: dict) -> dict:
    """Feed ALL gathered analysis into the final report prompt."""
    if state.get('error'):
        return {'report': f"⚠️ Analysis failed:\n```\n{state['error']}\n```"}
    prompt = prompts.COMPILE_REPORT_PROMPT.format(
        tech_stack=json.dumps(state.get('tech_stack', {}), indent=2),
        entry_points=state.get('entry_points', ''),
        module_summaries=state.get('module_summaries', ''),
        data_flow=state.get('data_flow', ''),
        gotchas=state.get('gotchas', ''),
        structure=state['structure'],
    )
    return {'report': _call_gemini(state['api_key'], prompt)}
