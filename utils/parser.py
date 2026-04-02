"""
Code parser using tree-sitter to extract structural info (classes, functions, imports).
Gracefully degrades if a language grammar is unavailable.
"""
import os
from tree_sitter import Language, Parser

# ---------------------------------------------------------------------------
# Lazy-load language grammars so the app still starts even when a grammar
# package is missing or has an incompatible API.
# ---------------------------------------------------------------------------

_LANGUAGES: dict[str, Language | None] = {}


def _load_languages():
    """Populate _LANGUAGES once."""
    if _LANGUAGES:
        return

    # Python
    try:
        import tree_sitter_python as _tspy
        _LANGUAGES['.py'] = Language(_tspy.language())
    except Exception:
        _LANGUAGES['.py'] = None

    # JavaScript
    try:
        import tree_sitter_javascript as _tsjs
        _LANGUAGES['.js'] = Language(_tsjs.language())
        _LANGUAGES['.jsx'] = _LANGUAGES['.js']
    except Exception:
        _LANGUAGES['.js'] = None
        _LANGUAGES['.jsx'] = None

    # TypeScript – the package exposes language_typescript / language_tsx
    try:
        import tree_sitter_typescript as _tsts
        try:
            _LANGUAGES['.ts'] = Language(_tsts.language_typescript())
        except AttributeError:
            _LANGUAGES['.ts'] = Language(_tsts.language())
        try:
            _LANGUAGES['.tsx'] = Language(_tsts.language_tsx())
        except AttributeError:
            _LANGUAGES['.tsx'] = _LANGUAGES['.ts']
    except Exception:
        _LANGUAGES['.ts'] = None
        _LANGUAGES['.tsx'] = None


def _get_parser(ext: str) -> Parser | None:
    _load_languages()
    lang = _LANGUAGES.get(ext)
    if lang is None:
        return None
    parser = Parser()
    parser.language = lang
    return parser


def extract_code_info(file_path: str) -> dict | None:
    """
    Returns {'classes': [...], 'functions': [...], 'imports': [...]}
    for supported file types, or None.
    """
    _, ext = os.path.splitext(file_path)
    parser = _get_parser(ext)
    if parser is None:
        return None

    try:
        with open(file_path, 'rb') as fh:
            source = fh.read()
    except Exception:
        return None

    tree = parser.parse(source)

    info: dict[str, list[str]] = {'classes': [], 'functions': [], 'imports': []}

    def _walk(node):
        # Classes
        if node.type in ('class_definition', 'class_declaration'):
            name = node.child_by_field_name('name')
            if name:
                info['classes'].append(source[name.start_byte:name.end_byte].decode())
        # Functions / methods
        elif node.type in (
            'function_definition', 'function_declaration',
            'method_definition', 'arrow_function',
        ):
            name = node.child_by_field_name('name')
            if name:
                info['functions'].append(source[name.start_byte:name.end_byte].decode())
        # Imports
        elif node.type in (
            'import_statement', 'import_from_statement',
            'import_declaration',
        ):
            info['imports'].append(source[node.start_byte:node.end_byte].decode())

        for child in node.children:
            _walk(child)

    _walk(tree.root_node)
    return info
