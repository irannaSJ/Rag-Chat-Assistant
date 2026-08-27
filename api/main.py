from fastapi import FastAPI, UploadFile, File 
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from ingestion.pdf_loader import load_pdf
from ingestion.notes_loader import load_notes
from ingestion.website_loader import load_website
from processing.chunker import chunk_text
from embeddings.embedder import Embedder
from vectorstore.faiss_store import FAISSVectorStore
from retriever.retriever import Retriever
from prompts.rag_prompt import build_rag_prompt
from llm.llm_client import LLMClient

import shutil
import os 

app = FastAPI(title = "RAG System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)


embedder = Embedder()
vector_store = None

class WebsiteIngestRequest(BaseModel):
    url:str
class ChatRequest(BaseModel):
    query : str

@app.post("/ingest/pdf")
async def ingest_pdf(file:UploadFile = File(...)):
    os.makedirs("data/raw/pdf",exist_ok = True)
    file_path = f"data/raw/pdf/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    documents = load_pdf(file_path)
    _build_vector_store(documents)

    return {"status": "PDF ingested successfully"}

@app.post("/ingest/notes")
async def ingest_notes(file:UploadFile = File(...)):
    os.makedirs("data/raw/notes",exist_ok=True)
    file_path = f"data/raw/notes/{file.filename}"

    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    documents = load_notes(file_path)
    _build_vector_store(documents)
    return {"status":"Notes ingested successfully"}

@app.post("/ingest/website")
async def ingest_website(data: WebsiteIngestRequest):
    documents = load_website(data.url)
    _build_vector_store(documents)

    return {"status":"Website ingested successfully"}


@app.post("/chat")
async def chat(data : ChatRequest):
    if vector_store is None:
        return {"error":"No data ingested yet"}

    retriever = Retriever(embedder, vector_store)
    retrieved_chunks = retriever.retrieve(data.query)

    prompt = build_rag_prompt(data.query, retrieved_chunks)
    llm = LLMClient()
    answer = llm.generate(prompt)
    return {"answer":answer}


#adding chat_stream endpoint for streaming 

@app.post("/chat-stream")
async def chat_stream(data:ChatRequest):
    def error_stream():
        yield "No data ingested yet. Please Ingest a document first."
    # if vector_store is None:
    #     return {"error":"No data ingested yet"}
    if  vector_store is None:
        return StreamingResponse(error_stream(),media_type="text/plain")

    retriever = Retriever(embedder, vector_store)
    retrieved_chunks = retriever.retrieve(data.query)

    if not retrieved_chunks:
        def empty_stream():
            yield "I don't know based on the provided information."
        return StreamingResponse(empty_stream(),media_type="text/plain")


    prompt = build_rag_prompt(data.query, retrieved_chunks)
    llm = LLMClient()

    def stream():
        for token in llm.generate_stream(prompt):
            yield token

    return StreamingResponse(stream(), media_type="text/plain")


def _build_vector_store(documents):
    global vector_store

    all_chunks = []
    for doc in documents:
        chunks = chunk_text(doc["text"],doc["metadata"])
        all_chunks.extend(chunks)

    embedded_chunks = embedder.embed_chunks(all_chunks)
    vector_dim = embedded_chunks[0]["vector"].shape[0]

    vector_store = FAISSVectorStore(vector_dim)
    vector_store.add_embeddings(embedded_chunks)