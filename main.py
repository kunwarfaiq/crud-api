"""Task API – a simple in-memory CRUD to-do service built with FastAPI."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    """Return a friendly hello message."""
    return {"message": "Hello from the Task API!"}
