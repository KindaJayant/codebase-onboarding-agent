import git
import os
import shutil

# Directories / files we never want to descend into
EXCLUDE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv',
    'env', 'dist', 'build', '.next', '.nuxt', '.cache',
    'coverage', '.tox', 'eggs', '*.egg-info',
}

# Files that are strong signals about a project's tech stack
KEY_FILE_NAMES = {
    'README.md', 'readme.md', 'README.rst',
    'package.json', 'package-lock.json', 'yarn.lock',
    'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile',
    'tsconfig.json', 'vite.config.ts', 'vite.config.js',
    'next.config.js', 'next.config.mjs',
    'docker-compose.yml', 'docker-compose.yaml', 'Dockerfile',
    'Makefile', 'Cargo.toml', 'go.mod',
    'main.py', 'app.py', 'manage.py', 'server.py',
    'index.js', 'index.ts', 'index.tsx',
    '.env.example', 'config.yaml', 'config.json',
}


def clone_repo(repo_url: str, local_path: str):
    """Clone a public GitHub repository.  Deletes any prior clone at *local_path*."""
    if os.path.exists(local_path):
        shutil.rmtree(local_path, ignore_errors=True)
    os.makedirs(local_path, exist_ok=True)
    return git.Repo.clone_from(repo_url, local_path, depth=1)


def get_file_tree(repo_path: str, max_depth: int = 5) -> str:
    """Return an indented, human-readable file tree (excludes noise)."""
    lines: list[str] = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = sorted([d for d in dirs if d not in EXCLUDE_DIRS])
        depth = root.replace(repo_path, '').count(os.sep)
        if depth > max_depth:
            dirs.clear()
            continue
        indent = '│  ' * depth
        lines.append(f"{indent}📁 {os.path.basename(root)}/")
        sub_indent = '│  ' * (depth + 1)
        for f in sorted(files):
            lines.append(f"{sub_indent}{f}")
    return "\n".join(lines)


def get_key_files(repo_path: str) -> list[str]:
    """Return absolute paths of high-signal config / entry-point files."""
    found: list[str] = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f in KEY_FILE_NAMES:
                found.append(os.path.join(root, f))
    return found


def read_key_files(repo_path: str, max_chars_per_file: int = 3000) -> str:
    """Read the *contents* of key files and return them as a single block,
    truncating large files to keep the context window manageable."""
    paths = get_key_files(repo_path)
    parts: list[str] = []
    for p in paths:
        rel = os.path.relpath(p, repo_path)
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as fh:
                text = fh.read(max_chars_per_file)
            parts.append(f"--- {rel} ---\n{text}")
        except Exception:
            parts.append(f"--- {rel} --- (unreadable)")
    return "\n\n".join(parts) if parts else "(no key files found)"
