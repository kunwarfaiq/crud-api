"""Task API – a simple in-memory CRUD to-do service built with FastAPI."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    """Return API metadata."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health")
def health():
    """Health-check endpoint."""
    return {"status": "ok"}
