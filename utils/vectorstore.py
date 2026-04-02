"""
ChromaDB vector store for semantic code search.
Embeds codebase chunks using Google's Generative AI embedding model
and provides a query interface.
"""
import os
import uuid
import chromadb
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction

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


def initialize_vector_store(repo_path: str, repo_name: str, api_key: str):
    """
    Walk the repository, chunk each indexable file, embed via Google Generative AI,
    and upsert into a ChromaDB collection.
    """
    col_name = _sanitize_collection_name(repo_name)
    embedding_fn = GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name="models/text-embedding-004",
    )

    # Delete existing collection to re-index fresh
    try:
        _client.delete_collection(col_name)
    except Exception:
        pass

    collection = _client.get_or_create_collection(
        name=col_name,
        embedding_function=embedding_fn,
    )

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


def search_codebase(repo_name: str, query: str, api_key: str, n: int = 5):
    """
    Semantic search over the indexed codebase.
    Returns the raw ChromaDB QueryResult dict.
    """
    col_name = _sanitize_collection_name(repo_name)
    embedding_fn = GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name="models/text-embedding-004",
    )
    try:
        collection = _client.get_collection(name=col_name, embedding_function=embedding_fn)
        return collection.query(query_texts=[query], n_results=n)
    except Exception as e:
        return {'documents': [[]], 'metadatas': [[]], 'error': str(e)}
