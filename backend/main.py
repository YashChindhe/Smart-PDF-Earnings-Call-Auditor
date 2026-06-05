import os
import json
import asyncio
import threading
from typing import Any
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from pypdf import PdfReader
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv()

# Set LangChain Tracing variables if available in env
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "Earnings-Call-Auditor")

from database import init_db, get_db, UploadedFile, AuditRun, AuditCard
from agent import run_audit_stream

app = FastAPI(title="AI PDF Earnings Call Auditor Backend", version="1.0.0")

# Setup CORS for Vercel Frontend and Localhost Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Initialize DB tables
    init_db()
    
    # Programmatically spin up LiteLLM Proxy in a background thread if flagged
    if os.getenv("USE_LITELLM_PROXY") == "true":
        print("Starting local LiteLLM Proxy server...")
        try:
            from litellm.proxy.proxy_cli import run_proxy
            def start_proxy():
                # Runs the proxy on port 8001
                run_proxy(host="127.0.0.1", port=8001)
            
            thread = threading.Thread(target=start_proxy, daemon=True)
            thread.start()
            print("LiteLLM Proxy thread launched on port 8001.")
        except Exception as e:
            print(f"Could not start LiteLLM Proxy: {e}")

@app.get("/")
def read_root():
    return {"message": "AI Earnings Call Auditor API is running", "port": 7860}

# 1. Upload PDF and Extract Text
@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        pdf_reader = PdfReader(file.file)
        text_content = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_content += text + "\n"
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="The PDF contains no readable text.")
        
        # Save to Neon / local Database
        uploaded_file = UploadedFile(filename=file.filename, content_text=text_content)
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        
        return {
            "file_id": uploaded_file.id,
            "filename": uploaded_file.filename,
            "text": text_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

# 2. SSE Streaming Audit Endpoint
@app.get("/api/agent/audit")
async def audit_pdf_stream(
    file_id: int = Query(..., description="ID of the uploaded PDF to audit"),
    db: Session = Depends(get_db)
):
    # Retrieve the uploaded PDF content
    uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="Uploaded file not found.")

    # Create a new Audit Run entry
    audit_run = AuditRun(file_id=file_id, status="in_progress")
    db.add(audit_run)
    db.commit()
    db.refresh(audit_run)

    async def event_generator():
        # SSE expects data as string or formatted events. We will use a queue to pass events.
        event_queue = asyncio.Queue()

        async def stream_callback(event_type: str, payload: Any):
            # Put the message on the queue
            await event_queue.put({"event": event_type, "data": json.dumps(payload)})

        # Launch the LangGraph agent chain in the background
        # We need to run it in a way that respects async event loops
        task = asyncio.create_task(run_audit_stream(
            pdf_text=uploaded_file.content_text,
            db=db,
            audit_run_id=audit_run.id,
            stream_callback=stream_callback
        ))

        # Yield items from queue until the background task is complete and queue is empty
        while not task.done() or not event_queue.empty():
            try:
                # Wait for next event with a timeout to avoid hanging
                event_data = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                yield event_data
                event_queue.task_done()
            except asyncio.TimeoutError:
                # If nothing in queue, just yield a keep-alive comment or continue
                continue

        # Final check if there was any exception
        if task.exception():
            yield {"event": "error", "data": json.dumps(str(task.exception()))}
        else:
            yield {"event": "done", "data": json.dumps({"audit_run_id": audit_run.id})}

    return EventSourceResponse(event_generator())
