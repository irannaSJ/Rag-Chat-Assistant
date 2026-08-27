# def chunk_text(
#     text:str,
#     metadata:dict,
#     chunk_size:int=500,
#     overlap:int =100):
#     chunks = []
#     start = 0
#     chunk_id = 0
#     text_length = len(text)

#     while start < text_length:
#         end = start + chunk_size
#         chunk = text[start:end]

#         if chunk.strip():
#             chunk_metadata = metadata.copy()
#             chunk_metadata["chunk_id"] = chunk_id

#             chunks.append({
#                 "chunk_text":chunk,
#                 "metadata":chunk_metadata
#             })

#             chunk_id +=1
#             start +=chunk_size-overlap
#     return chunks


from transformers import AutoTokenizer

TOKENIZER_NAME = "sentence-transformers/all-MiniLM-L6-v2"

try:
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
except Exception:
    tokenizer = None

def _fallback_chunk_text(text: str, metadata: dict, chunk_size: int, overlap: int):
    chunks = []
    start = 0
    chunk_id = 0
    step = max(chunk_size - overlap, 1)

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = chunk_id
            chunks.append({
                "chunk_text": chunk,
                "metadata": chunk_metadata,
            })
            chunk_id += 1

        start += step

    return chunks

def chunk_text(
    text:str,
    metadata :dict,
    chunk_size : int = 256,
    overlap : int =50
    ):
    """
    Token-aware chunking
    """
    if tokenizer is None:
        return _fallback_chunk_text(text, metadata, chunk_size * 4, overlap * 4)

    tokens = tokenizer.encode(text,add_special_tokens=False)
    chunks = []
    start = 0
    chunk_id = 0


    while start<len(tokens):
        end = start+chunk_size
        chunk_tokens = tokens[start:end]

        chunk_text = tokenizer.decode(chunk_tokens)
        if chunk_text.strip():
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = chunk_id

            chunks.append({
                "chunk_text":chunk_text,
                "metadata":chunk_metadata
            })

            chunk_id +=1

        start +=chunk_size - overlap
    return chunks
