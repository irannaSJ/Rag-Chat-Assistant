def build_rag_prompt(query:str, retrieved_chunks:list) -> str:
    context_blocks = []

    for chunk in retrieved_chunks:
        meta = chunk["metadata"]
        source_info = []
    
        if "source_type" in meta:
            source_info.append(meta["source_type"])
        if "page" in meta:
            source_info.append(f"page {meta['page']}")
        if "url" in meta:
            source_info.append(meta["url"])

        source_line = " | ".join(source_info)

        # context_blocks.append(
        #     f"[Source : {source_line}] \n {chunk['chunk_text']}"
        # )
        MAX_CHUNK_CHARS = 800

        trimmed_text = chunk["chunk_text"][:MAX_CHUNK_CHARS]
        context_blocks.append(
            f"[Source: {source_line}]\n {trimmed_text}"
        )

    context_text = "\n\n".join(context_blocks)

    # prompt = f"""
    # You are a helpful assistant.
    # Answer the question ONLY using the context below.
    # If the answer is not present in the context, say:
    # "I dont't know based on the provided information."

    # Context:
    # {context_text}
    prompt = f"""
    You are an AI assistant answering questions using ONLY the provided context.

    Rules you MUST follow:
    - Use only the information in the context.
    - Do NOT use prior knowledge.
    - If the context does not contain the answer, say:
    "I don't know based on the provided information."
    - Do NOT mention that you are an AI or language model.

    Answering style:
    - Be clear and concise.
    - If the question asks for an explanation, answer in structured points.
    - If multiple facts are relevant, combine them logically.
    - The context may be partial: focus on the most relevant details.



    Context:
    {context_text}

    Question:
    {query}

    Answer:
    """.strip()

    return prompt