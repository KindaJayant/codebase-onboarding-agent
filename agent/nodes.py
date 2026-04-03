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
import tempfile
import time
from collections import Counter

from openai import OpenAI

from . import prompts
from utils import repo as repo_utils
from utils import parser as parser_utils

# ── Model Configuration ─────────────────────────────────────────────────────
OPENROUTER_MODEL = "qwen/qwen-2.5-72b-instruct"

# ── helpers ──────────────────────────────────────────────────────────────────

def _call_llm(api_key: str, prompt: str) -> str:
    """Send a single prompt to OpenRouter and return the text response."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                print(f"Rate limit hit. Pausing 15s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(15)
            else:
                raise e


def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction from LLM output."""
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
            
            # Protect Free Tier Limits
            if len("\n".join(summaries)) > 20000:
                summaries.append("\n--- [TRUNCATED: Repository too large. Preserving API limits.] ---")
                return "\n\n".join(summaries)
                
    return "\n\n".join(summaries) if summaries else "(tree-sitter analysis unavailable)"


def _compute_metrics(repo_path: str) -> dict:
    """Compute real repository metrics: file count, languages, LOC, dependencies."""
    total_files = 0
    ext_counter = Counter()
    total_loc = 0
    dep_count = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in repo_utils.EXCLUDE_DIRS]
        for fname in files:
            total_files += 1
            _, ext = os.path.splitext(fname)
            if ext:
                ext_counter[ext] += 1
            
            # Count lines for code files
            fpath = os.path.join(root, fname)
            if ext in ('.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.rb', '.css', '.html', '.md'):
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                        total_loc += sum(1 for _ in fh)
                except Exception:
                    pass

            # Count dependencies
            if fname == 'requirements.txt':
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                        dep_count += sum(1 for line in fh if line.strip() and not line.startswith('#'))
                except Exception:
                    pass
            elif fname == 'package.json':
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                        pkg = json.loads(fh.read())
                        dep_count += len(pkg.get('dependencies', {}))
                        dep_count += len(pkg.get('devDependencies', {}))
                except Exception:
                    pass

    # Build language breakdown from top extensions
    EXT_TO_LANG = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.tsx': 'TSX', '.jsx': 'JSX', '.java': 'Java', '.go': 'Go',
        '.rs': 'Rust', '.rb': 'Ruby', '.css': 'CSS', '.html': 'HTML',
        '.md': 'Markdown', '.json': 'JSON', '.yaml': 'YAML', '.yml': 'YAML',
        '.toml': 'TOML', '.sql': 'SQL', '.sh': 'Shell', '.c': 'C', '.cpp': 'C++',
    }

    code_exts = {k: v for k, v in ext_counter.items() if k in EXT_TO_LANG}
    total_code_files = sum(code_exts.values()) or 1
    top_langs = sorted(code_exts.items(), key=lambda x: x[1], reverse=True)[:4]
    
    lang_breakdown = []
    for ext, count in top_langs:
        pct = round(count / total_code_files * 100)
        lang_breakdown.append(f"{EXT_TO_LANG.get(ext, ext)} ({pct}%)")

    unique_langs = len(set(EXT_TO_LANG.get(ext, ext) for ext in code_exts.keys()))

    return {
        'total_files': total_files,
        'languages': unique_langs,
        'lang_breakdown': ', '.join(lang_breakdown) if lang_breakdown else 'N/A',
        'loc': total_loc,
        'dependencies': dep_count,
    }


# ── nodes ────────────────────────────────────────────────────────────────────

def parse_structure(state: dict) -> dict:
    """Clone the repo, generate the file tree, read key files, run tree-sitter, compute metrics."""
    try:
        repo_name = state['repo_name']
        repo_url = state['repo_url']
        
        temp_dir = tempfile.mkdtemp(prefix="codebase_agent_")
        repo_path = os.path.abspath(os.path.join(temp_dir, repo_name))

        repo_utils.clone_repo(repo_url, repo_path)

        structure = repo_utils.get_file_tree(repo_path)
        key_files_content = repo_utils.read_key_files(repo_path)
        code_info = _collect_code_info(repo_path)
        metrics = _compute_metrics(repo_path)

        return {
            'repo_path': repo_path,
            'structure': structure,
            'key_files_content': key_files_content,
            'code_info': code_info,
            'metrics': metrics,
        }
    except Exception as e:
        return {'error': f"Clone/parse failed: {e}\n{traceback.format_exc()}"}


def identify_tech_stack(state: dict) -> dict:
    """Ask LLM to identify the tech stack and return parsed JSON."""
    if state.get('error'):
        return {}
    prompt = prompts.TECH_STACK_PROMPT.format(
        structure=state['structure'],
        key_files_content=state['key_files_content'],
    )
    raw = _call_llm(state['api_key'], prompt)
    return {'tech_stack': _extract_json(raw)}


def find_entry_points(state: dict) -> dict:
    if state.get('error'):
        return {}
    prompt = prompts.ENTRY_POINTS_PROMPT.format(
        structure=state['structure'],
        key_files_content=state['key_files_content'],
        code_info=state.get('code_info', ''),
    )
    return {'entry_points': _call_llm(state['api_key'], prompt)}


def summarize_modules(state: dict) -> dict:
    if state.get('error'):
        return {}
    prompt = prompts.MODULE_SUMMARIES_PROMPT.format(
        structure=state['structure'],
        key_files_content=state['key_files_content'],
    )
    return {'module_summaries': _call_llm(state['api_key'], prompt)}


def trace_data_flow(state: dict) -> dict:
    if state.get('error'):
        return {}
    prompt = prompts.DATA_FLOW_PROMPT.format(
        tech_stack=json.dumps(state.get('tech_stack', {}), indent=2),
        entry_points=state.get('entry_points', ''),
        module_summaries=state.get('module_summaries', ''),
        structure=state['structure'],
    )
    return {'data_flow': _call_llm(state['api_key'], prompt)}


def extract_caveats(state: dict) -> dict:
    if state.get('error'):
        return {}
    prompt = prompts.CAVEATS_PROMPT.format(
        structure=state['structure'],
        tech_stack=json.dumps(state.get('tech_stack', {}), indent=2),
        key_files_content=state['key_files_content'],
    )
    return {'caveats': _call_llm(state['api_key'], prompt)}


def compile_report(state: dict) -> dict:
    """Feed ALL gathered analysis into the final report prompt."""
    if state.get('error'):
        return {'report': f"⚠️ Analysis failed:\n```\n{state['error']}\n```"}
    prompt = prompts.COMPILE_REPORT_PROMPT.format(
        tech_stack=json.dumps(state.get('tech_stack', {}), indent=2),
        entry_points=state.get('entry_points', ''),
        module_summaries=state.get('module_summaries', ''),
        data_flow=state.get('data_flow', ''),
        caveats=state.get('caveats', ''),
        structure=state['structure'],
    )
    return {'report': _call_llm(state['api_key'], prompt)}
