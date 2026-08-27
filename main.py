# main.py

from ingestion.pdf_loader import load_pdf
from ingestion.notes_loader import load_notes
from ingestion.website_loader import load_website

from processing.chunker import chunk_text

from embeddings.embedder import Embedder
from vectorstore.faiss_store import FAISSVectorStore
from retriever.retriever import Retriever
from prompts.rag_prompt import build_rag_prompt
from llm.llm_client import LLMClient


def ingest_data(source_type: str, source_value: str):
    if source_type == "PDF":
        return load_pdf(source_value)
    elif source_type == "NOTES":
        return load_notes(source_value)
    elif source_type == "WEBSITE":
        return load_website(source_value)
    else:
        raise ValueError("Unsupported source type")


def build_vector_store(documents):
    all_chunks = []

    for doc in documents:
        chunks = chunk_text(
            text=doc["text"],
            metadata=doc["metadata"]
        )
        all_chunks.extend(chunks)

    embedder = Embedder()
    embedded_chunks = embedder.embed_chunks(all_chunks)

    vector_dim = embedded_chunks[0]["vector"].shape[0]
    vector_store = FAISSVectorStore(vector_dim=vector_dim)

    vector_store.add_embeddings(embedded_chunks)

    return embedder, vector_store


def run_query(query: str, embedder, vector_store):
    retriever = Retriever(embedder, vector_store)
    retrieved_chunks = retriever.retrieve(query)

    prompt = build_rag_prompt(query, retrieved_chunks)

    llm = LLMClient()
    answer = llm.generate(prompt)

    return answer


if __name__ == "__main__":
    print("Select data source:")
    print("1. PDF")
    print("2. NOTES")
    print("3. WEBSITE")

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == "1":
        source_type = "PDF"
        source_value = input("Enter PDF file path: ").strip()
    elif choice == "2":
        source_type = "NOTES"
        source_value = input("Enter notes file path: ").strip()
    elif choice == "3":
        source_type = "WEBSITE"
        source_value = input("Enter website URL: ").strip()
    else:
        raise ValueError("Invalid choice")

    print("\nIngesting data...")
    documents = ingest_data(source_type, source_value)

    print("Building vector store...")
    embedder, vector_store = build_vector_store(documents)

    print("\nRAG system ready! Ask questions (type 'exit' to quit)\n")

    while True:
        query = input("You: ").strip()
        if query.lower() == "exit":
            break

        answer = run_query(query, embedder, vector_store)
        print("\nAssistant:", answer, "\n")
