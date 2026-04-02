"""
ChromaDB vector store for semantic code search.
Uses ChromaDB's default local ONNX embedding model (all-MiniLM-L6-v2)
so no external API key is needed for embeddings.
"""
import os
import uuid
import chromadb

# Extensions we index
INDEXABLE_EXTS = {'.py', '.js', '.ts', '.tsx', '.jsx', '.md', '.txt', '.yaml', '.yml', '.json', '.toml', '.cfg'}

# Folders to skip while indexing
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.next'}

# ChromaDB persistent client – stored in project-level ./db folder
_client = chromadb.PersistentClient(path="./db")


def _sanitize_collection_name(name: str) -> str:
    """ChromaDB collection names must be 3-63 chars, start/end with alphanum."""
    name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
    name = name.strip('_-') or 'default'
    return name[:63] if len(name) >= 3 else name.ljust(3, '_')


def initialize_vector_store(repo_path: str, repo_name: str):
    """
    Walk the repository, chunk each indexable file,
    and upsert into a ChromaDB collection using default local embeddings.
    """
    col_name = _sanitize_collection_name(repo_name)

    # Delete existing collection to re-index fresh
    try:
        _client.delete_collection(col_name)
    except Exception:
        pass

    collection = _client.get_or_create_collection(name=col_name)

    docs, ids, metas = [], [], []
    chunk_size, overlap = 800, 150

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            _, ext = os.path.splitext(fname)
            if ext not in INDEXABLE_EXTS:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                    content = fh.read()
            except Exception:
                continue

            rel_path = os.path.relpath(fpath, repo_path)
            step = max(chunk_size - overlap, 1)
            for i in range(0, max(len(content), 1), step):
                chunk = content[i:i + chunk_size].strip()
                if not chunk:
                    continue
                docs.append(chunk)
                ids.append(str(uuid.uuid4()))
                metas.append({'file': rel_path, 'repo': repo_name, 'offset': i})

    # ChromaDB limits batch size to ~5461, so chunk the upsert
    BATCH = 5000
    for i in range(0, len(docs), BATCH):
        collection.add(
            documents=docs[i:i + BATCH],
            metadatas=metas[i:i + BATCH],
            ids=ids[i:i + BATCH],
        )

    return collection


def search_codebase(repo_name: str, query: str, n: int = 5):
    """
    Semantic search over the indexed codebase using local embeddings.
    Returns the raw ChromaDB QueryResult dict.
    """
    col_name = _sanitize_collection_name(repo_name)
    try:
        collection = _client.get_collection(name=col_name)
        return collection.query(query_texts=[query], n_results=n)
    except Exception as e:
        return {'documents': [[]], 'metadatas': [[]], 'error': str(e)}
