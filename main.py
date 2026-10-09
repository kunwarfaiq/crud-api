"""Task API – a simple in-memory CRUD to-do service built with FastAPI."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# ---------------------------------------------------------------------------
# In-memory task store
# ---------------------------------------------------------------------------
tasks: list[dict] = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Walk the dog", "done": False},
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _find_task(task_id: int) -> dict | None:
    """Return a task dict by id, or None."""
    return next((t for t in tasks if t["id"] == task_id), None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
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


@app.get("/tasks")
def list_tasks():
    """Return every task in the store."""
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Return a single task by its id, or 404."""
    task = _find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )
    return task
