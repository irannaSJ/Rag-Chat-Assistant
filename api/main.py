from contextlib import asynccontextmanager
import json
import os
import shutil
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from embeddings.embedder import Embedder
from ingestion.notes_loader import load_notes_file, load_notes_text
from ingestion.pdf_loader import load_pdf
from ingestion.website_loader import load_website
from llm.llm_client import LLMClient
from processing.chunker import chunk_text
from prompts.rag_prompt import build_rag_prompt, format_sources
from retriever.retriever import Retriever
from vectorstore.faiss_store import FAISSVectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedder = Embedder()
    vector_store = FAISSVectorStore(vector_dim=embedder.dimension)
    vector_store.load()

    app.state.embedder = embedder
    app.state.vector_store = vector_store
    yield


app = FastAPI(title="Multi-Document RAG API", version="0.2.0", lifespan=lifespan)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

extra_origins = os.getenv("ALLOWED_ORIGINS", "")
if extra_origins:
    allowed_origins.extend([origin.strip() for origin in extra_origins.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebsiteIngestRequest(BaseModel):
    url: str


class TextNoteIngestRequest(BaseModel):
    title: str = "Quick Note"
    content: str


class ChatRequest(BaseModel):
    query: str
    top_k: int = 4


def _ingest_documents(documents: list[dict], source_id: str) -> dict:
    if not documents:
        raise HTTPException(
            status_code=422,
            detail="No readable text could be extracted from this source.",
        )

    all_chunks = []
    for doc in documents:
        meta = doc["metadata"].copy()
        meta["source_id"] = source_id
        chunks = chunk_text(doc["text"], meta)
        all_chunks.extend(chunks)

    if not all_chunks:
        raise HTTPException(
            status_code=422,
            detail="Document contained no valid text chunks after processing.",
        )

    embedder: Embedder = app.state.embedder
    vector_store: FAISSVectorStore = app.state.vector_store

    embedded_chunks = embedder.embed_chunks(all_chunks)
    vector_store.add_embeddings(embedded_chunks)

    first_meta = documents[0]["metadata"]
    return {
        "status": "Ingested successfully",
        "source": {
            "source_id": source_id,
            "source_name": first_meta.get("source_name", "Untitled"),
            "source_type": first_meta.get("source_type", "UNKNOWN"),
            "url": first_meta.get("url"),
            "chunk_count": len(all_chunks),
        },
        "total_sources": len(vector_store.list_sources()),
    }


@app.get("/health")
async def health():
    vector_store: FAISSVectorStore = app.state.vector_store
    return {
        "status": "ok",
        "total_chunks": vector_store.total_chunks,
        "total_sources": len(vector_store.list_sources()),
    }


@app.get("/sources")
async def get_sources():
    vector_store: FAISSVectorStore = app.state.vector_store
    return {
        "sources": vector_store.list_sources(),
        "total_chunks": vector_store.total_chunks,
    }


@app.delete("/sources/{source_id}")
async def remove_source(source_id: str):
    vector_store: FAISSVectorStore = app.state.vector_store
    deleted = vector_store.delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return {
        "status": "Source removed",
        "sources": vector_store.list_sources(),
    }


@app.delete("/sources")
async def clear_all_sources():
    vector_store: FAISSVectorStore = app.state.vector_store
    vector_store.clear()
    return {"status": "All sources cleared", "sources": []}


@app.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs("data/raw/pdf", exist_ok=True)
    source_id = f"pdf_{uuid.uuid4().hex[:10]}"
    safe_path = f"data/raw/pdf/{source_id}_{os.path.basename(file.filename)}"

    try:
        with open(safe_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        documents = load_pdf(safe_path, source_name=file.filename)
        return _ingest_documents(documents, source_id=source_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(exc)}")


@app.post("/ingest/notes")
async def ingest_notes_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    os.makedirs("data/raw/notes", exist_ok=True)
    source_id = f"note_{uuid.uuid4().hex[:10]}"
    safe_path = f"data/raw/notes/{source_id}_{os.path.basename(file.filename)}"

    try:
        with open(safe_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        documents = load_notes_file(safe_path, source_name=file.filename)
        return _ingest_documents(documents, source_id=source_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process notes file: {str(exc)}")


@app.post("/ingest/notes/text")
async def ingest_notes_raw(data: TextNoteIngestRequest):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Note content cannot be empty.")

    source_id = f"note_{uuid.uuid4().hex[:10]}"
    documents = load_notes_text(data.content, source_name=data.title)
    return _ingest_documents(documents, source_id=source_id)


@app.post("/ingest/website")
async def ingest_website(data: WebsiteIngestRequest):
    url = data.url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        source_id = f"web_{uuid.uuid4().hex[:10]}"
        documents = load_website(url)
        return _ingest_documents(documents, source_id=source_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch website: {str(exc)}")


@app.post("/chat")
async def chat(data: ChatRequest):
    vector_store: FAISSVectorStore = app.state.vector_store
    embedder: Embedder = app.state.embedder

    if vector_store.total_chunks == 0:
        raise HTTPException(status_code=400, detail="No documents ingested yet.")

    retriever = Retriever(embedder, vector_store, top_k=data.top_k)
    retrieved_chunks = retriever.retrieve(data.query)

    if not retrieved_chunks:
        return {
            "answer": "I couldn't find enough information in your uploaded sources to answer that.",
            "sources": [],
        }

    prompt = build_rag_prompt(data.query, retrieved_chunks)
    llm = LLMClient()
    answer = llm.generate(prompt)

    return {
        "answer": answer,
        "sources": format_sources(retrieved_chunks),
    }


@app.post("/chat-stream")
async def chat_stream(data: ChatRequest):
    vector_store: FAISSVectorStore = app.state.vector_store
    embedder: Embedder = app.state.embedder

    def ndjson_line(payload: dict) -> str:
        return json.dumps(payload, ensure_ascii=False) + "\n"

    if vector_store.total_chunks == 0:
        def empty_store_stream():
            yield ndjson_line({
                "type": "token",
                "content": "No documents ingested yet. Please upload a PDF, note, or website first.",
            })
        return StreamingResponse(
            empty_store_stream(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    retriever = Retriever(embedder, vector_store, top_k=data.top_k)
    retrieved_chunks = retriever.retrieve(data.query)

    if not retrieved_chunks:
        def no_match_stream():
            yield ndjson_line({"type": "sources", "sources": []})
            yield ndjson_line({
                "type": "token",
                "content": "I couldn't find enough information in your uploaded sources to answer that.",
            })
        return StreamingResponse(
            no_match_stream(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    sources = format_sources(retrieved_chunks)
    prompt = build_rag_prompt(data.query, retrieved_chunks)
    llm = LLMClient()

    def stream():
        yield ndjson_line({"type": "sources", "sources": sources})
        for token in llm.generate_stream(prompt):
            yield ndjson_line({"type": "token", "content": token})

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )