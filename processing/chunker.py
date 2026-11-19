import re


def _token_len(text: str) -> int:
    """Fast subword token estimate (~1.3 tokens per word)."""
    words = re.findall(r"\S+", text)
    return max(1, int(len(words) * 1.3))


def _split_segments(text: str) -> list[str]:
    """Split text into paragraphs first, breaking oversized paragraphs into sentences."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    segments: list[str] = []

    for para in paragraphs:
        if _token_len(para) <= 200:
            segments.append(para)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            segments.extend(s.strip() for s in sentences if s.strip())

    return segments


def _hard_split_by_words(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Fallback splitter for single huge blocks without punctuation."""
    words = text.split()
    max_words = max(int(chunk_size / 1.3), 1)
    overlap_words = max(int(overlap / 1.3), 0)
    step = max(max_words - overlap_words, 1)

    pieces = []
    for start in range(0, len(words), step):
        piece = " ".join(words[start : start + max_words]).strip()
        if piece:
            pieces.append(piece)
    return pieces


def chunk_text(
    text: str,
    metadata: dict,
    chunk_size: int = 256,
    overlap: int = 40,
) -> list[dict]:
    """Paragraph & sentence-aware chunking with overlap."""
    if not text or not text.strip():
        return []

    segments = _split_segments(text)
    raw_chunks: list[str] = []
    current_segments: list[str] = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = _token_len(seg)

        if seg_tokens > chunk_size:
            if current_segments:
                raw_chunks.append("\n\n".join(current_segments))
                current_segments = []
                current_tokens = 0
            raw_chunks.extend(_hard_split_by_words(seg, chunk_size, overlap))
            continue

        if current_tokens + seg_tokens > chunk_size and current_segments:
            raw_chunks.append("\n\n".join(current_segments))

            overlap_segments: list[str] = []
            overlap_tokens = 0
            for prev_seg in reversed(current_segments):
                prev_len = _token_len(prev_seg)
                if overlap_tokens + prev_len <= overlap:
                    overlap_segments.insert(0, prev_seg)
                    overlap_tokens += prev_len
                else:
                    break

            current_segments = overlap_segments
            current_tokens = overlap_tokens

        current_segments.append(seg)
        current_tokens += seg_tokens

    if current_segments:
        raw_chunks.append("\n\n".join(current_segments))

    chunks = []
    for chunk_id, chunk_str in enumerate(raw_chunks):
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk_id"] = chunk_id
        chunks.append({
            "chunk_text": chunk_str,
            "metadata": chunk_metadata,
        })

    return chunks