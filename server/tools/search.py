"""Semantic search over the vault via LanceDB."""
from typing import Optional
from mcp_instance import mcp
from config import settings


def _get_table():
    """Lazy-load the LanceDB table."""
    try:
        import lancedb
        db = lancedb.connect(str(settings.INDEX_PATH))
        return db.open_table("vault")
    except Exception as e:
        return None, str(e)


def _embed(text: str) -> list:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(settings.EMBED_MODEL)
    return model.encode(text).tolist()


@mcp.tool()
def search_knowledge(
    query: str,
    subject: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = 5,
) -> str:
    """
    Semantic search across all vault content: notes, exams, campaigns, normative.
    Returns the most relevant chunks with source file references.

    query: what you're looking for (natural language).
    subject: optional filter by subject folder name.
    content_type: optional filter — 'notes', 'exam', 'normative', 'campaign'.
    limit: max results (default 5).
    """
    result = _get_table()
    if isinstance(result, tuple):
        table, err = result
        if table is None:
            return (
                f"Vector index not available: {err}\n"
                "Run `scripts/build_index.py` to build it, or check that INDEX_PATH is correct."
            )
    else:
        table = result

    try:
        query_vec = _embed(query)
        search = table.search(query_vec).limit(limit)

        if subject:
            search = search.where(f"subject = '{subject}'")
        if content_type:
            search = search.where(f"type = '{content_type}'")

        results = search.to_list()
    except Exception as e:
        return f"Search failed: {e}"

    if not results:
        return "No results found. Try different search terms or check the index."

    lines = [f"## Search Results: '{query}'\n"]
    for i, r in enumerate(results, 1):
        score = round(1 - r.get("_distance", 1), 3)
        source = r.get("file_path", "unknown")
        topic = r.get("topic", "")
        content = r.get("content", "")[:400]
        lines.append(
            f"### {i}. {topic or source} (relevance: {score})\n"
            f"Source: `{source}`\n\n{content}...\n"
        )

    return "\n".join(lines)
