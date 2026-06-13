"""LanceDB indexer — build and update the vector index from vault markdown files."""
from pathlib import Path
from typing import Optional
import hashlib


VECTOR_DIM = 384  # all-MiniLM-L6-v2 output dimension
TABLE_NAME = "vault"


def _get_db(index_path: str):
    import lancedb
    return lancedb.connect(index_path)


def _embed(texts: list[str], model=None) -> list:
    from sentence_transformers import SentenceTransformer
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model.encode(texts, show_progress_bar=False).tolist()


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks for better retrieval."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks or [text]


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def parse_vault_file(md_path: Path, vault_root: Path) -> list[dict]:
    """Parse a markdown file with frontmatter into indexable records."""
    import frontmatter

    try:
        post = frontmatter.load(str(md_path))
    except Exception:
        return []

    meta = post.metadata
    content = post.content.strip()
    if not content:
        return []

    rel_path = str(md_path.relative_to(vault_root))
    chunks = _chunk_text(content)

    records = []
    for i, chunk in enumerate(chunks):
        chunk_id = f"{_file_hash(md_path)}-{i}"
        records.append({
            "id": chunk_id,
            "file_path": rel_path,
            "content": chunk,
            "type": str(meta.get("type", "unknown") or ""),
            "subject": str(meta.get("subject", "") or ""),
            "semester": str(meta.get("semester", "") or ""),
            "topic": str(meta.get("topic", "") or ""),
            "source": str(meta.get("source", "") or ""),
            "quality": str(meta.get("quality", "") or ""),
            "date_added": str(meta.get("date_added", "") or ""),
        })
    return records


def build_index(vault_path: str, index_path: str, model=None) -> dict:
    """
    Full rebuild of the LanceDB index from all markdown files in the vault.
    Skips config/, ingest/, and non-content files.
    """
    import lancedb
    import pyarrow as pa
    from sentence_transformers import SentenceTransformer

    vault = Path(vault_path)
    db = _get_db(index_path)
    model = model or SentenceTransformer("all-MiniLM-L6-v2")

    # Collect all markdown files (skip ingest/ and raw dirs)
    md_files = [
        p for p in vault.rglob("*.md")
        if "ingest" not in p.parts and "raw" not in p.parts and p.name != "CLAUDE.md"
    ]

    all_records = []
    for md_path in md_files:
        all_records.extend(parse_vault_file(md_path, vault))

    if not all_records:
        return {"indexed": 0, "files": 0, "status": "empty vault"}

    # Embed in batches to avoid OOM on memory-constrained servers
    texts = [r["content"] for r in all_records]
    vectors = []
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        vectors.extend(_embed(texts[i:i + batch_size], model))
    for record, vec in zip(all_records, vectors):
        record["vector"] = vec

    # Schema
    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("file_path", pa.string()),
        pa.field("content", pa.string()),
        pa.field("type", pa.string()),
        pa.field("subject", pa.string()),
        pa.field("semester", pa.string()),
        pa.field("topic", pa.string()),
        pa.field("source", pa.string()),
        pa.field("quality", pa.string()),
        pa.field("date_added", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), VECTOR_DIM)),
    ])

    # Drop and recreate table
    try:
        db.drop_table(TABLE_NAME)
    except Exception:
        pass

    table = db.create_table(TABLE_NAME, data=all_records, schema=schema)

    return {
        "indexed": len(all_records),
        "files": len(md_files),
        "status": "ok",
    }


def upsert_document(record: dict, index_path: str, model=None) -> bool:
    """Add or update a single document in the index."""
    import lancedb
    from sentence_transformers import SentenceTransformer

    if not record.get("content"):
        return False

    model = model or SentenceTransformer("all-MiniLM-L6-v2")
    vector = _embed([record["content"]], model)[0]
    record["vector"] = vector

    db = _get_db(index_path)
    try:
        table = db.open_table(TABLE_NAME)
        # Delete existing record with same id if present
        table.delete(f"id = '{record['id']}'")
        table.add([record])
    except Exception:
        # Table doesn't exist yet — do a full build
        return False

    return True
