"""
Prompt templates for each analysis stage.
All templates use str.format() with named placeholders.
"""

TECH_STACK_PROMPT = """\
You are a senior software engineer onboarding onto a new codebase.

Based on the repository's file tree and key file contents below, identify the
complete tech stack.  Return **only** valid JSON (no markdown fences) with these keys:
{{
  "primary_language": "...",
  "framework": "...",
  "secondary_libs": ["..."],
  "database": "... or null",
  "frontend": "... or null",
  "testing": "... or null",
  "build_tools": "... or null",
  "containerization": "... or null"
}}

### File Tree
{structure}

### Key File Contents
{key_files_content}
"""

ENTRY_POINTS_PROMPT = """\
You are onboarding a senior developer onto this codebase.

Identify **all** entry points: API servers, CLI commands, scheduled jobs,
event handlers, etc.  For each entry point state:
1. File path and function/class name
2. What it does (one sentence)
3. How to invoke it (e.g. `python manage.py runserver`, `npm start`)

### File Tree
{structure}

### Key File Contents
{key_files_content}

### Extracted Code Symbols
{code_info}
"""

MODULE_SUMMARIES_PROMPT = """\
Summarize the logical modules / packages in this repository.
Group them by feature domain (e.g. auth, storage, api, models, utils).
For each module, give its directory path and a 1-2 sentence description.

### File Tree
{structure}

### Key File Contents
{key_files_content}
"""

DATA_FLOW_PROMPT = """\
Trace the typical data flow for a **core feature** of this application.
Start from the external trigger (HTTP request, CLI invocation, event) and
follow the data through middleware, controllers, services, models, and
external dependencies.  Use arrows (→) to show the flow.

If you can, provide a Mermaid flowchart diagram as well.

### Tech Stack
{tech_stack}

### Entry Points
{entry_points}

### Module Summaries
{module_summaries}

### File Tree
{structure}
"""

GOTCHAS_PROMPT = """\
Identify potential "gotchas" and things that would trip up a new developer:
- Non-obvious configuration requirements
- Complex dependency chains
- Environment variables that MUST be set
- Database migration steps
- Tricky deployment steps
- Areas where the code is fragile or tightly coupled

### File Tree
{structure}

### Tech Stack
{tech_stack}

### Key File Contents
{key_files_content}
"""

COMPILE_REPORT_PROMPT = """\
Compile a comprehensive **senior-developer-level onboarding report** in Markdown.

Use the following gathered analysis as your source material.  Do NOT
hallucinate information that isn't present — flag unknowns as "⚠️ Not determined".

Sections:
1. **Executive Summary** — what this project is and does (3-5 sentences)
2. **Tech Stack Overview** — table of languages, frameworks, databases, tools
3. **Entry Points & How to Run** — how to start / invoke the application
4. **Architecture & Module Map** — how the code is organized
5. **Data Flow** — end-to-end flow for a core feature (include Mermaid if possible)
6. **Developer Gotchas & Onboarding Tips** — things a new dev must know

---
### Tech Stack (raw)
{tech_stack}

### Entry Points
{entry_points}

### Module Summaries
{module_summaries}

### Data Flow
{data_flow}

### Gotchas
{gotchas}

### File Tree
{structure}
"""
