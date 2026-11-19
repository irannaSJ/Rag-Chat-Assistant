MAX_CHUNK_CHARS = 1200


def _format_source_label(meta: dict) -> str:
    source_name = meta.get("source_name", "Unknown Source")
    source_type = meta.get("source_type", "")

    if source_type == "PDF" and "page" in meta:
        return f"{source_name} (p. {meta['page']})"
    if source_type == "WEBSITE" and meta.get("url"):
        return f"{source_name} ({meta['url']})"
    return source_name


def format_sources(retrieved_chunks: list[dict]) -> list[dict]:
    """Return deduplicated source metadata for frontend citation badges."""
    seen = set()
    sources = []

    for chunk in retrieved_chunks:
        meta = chunk["metadata"]
        label = _format_source_label(meta)
        if label in seen:
            continue
        seen.add(label)
        sources.append({
            "label": label,
            "source_name": meta.get("source_name", "Unknown Source"),
            "source_type": meta.get("source_type", "UNKNOWN"),
            "page": meta.get("page"),
            "url": meta.get("url"),
            "score": round(chunk.get("score", 0.0), 3),
        })

    return sources


def build_rag_prompt(query: str, retrieved_chunks: list[dict]) -> str:
    context_blocks = []

    for chunk in retrieved_chunks:
        label = _format_source_label(chunk["metadata"])
        trimmed_text = chunk["chunk_text"][:MAX_CHUNK_CHARS]
        context_blocks.append(f"\n{trimmed_text}")

    context_text = "\n\n---\n\n".join(context_blocks)

    prompt = f"""Answer the user's question using ONLY the context provided below.

Guidelines:
- Ground every claim strictly in the provided context. Do not use outside knowledge.
- Use clear, well-structured Markdown (short paragraphs, bullet points, or bold key terms where helpful).
- Cite the source inline when referencing facts (e.g., [Document.pdf, p. 2]).
- If the context does not contain enough information to answer the question, reply with:
  "I couldn't find enough information in your uploaded sources to answer that."

Context:
{context_text}

Question:
{query}
""".strip()

    return prompt