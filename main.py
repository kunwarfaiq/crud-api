"""Task API – a simple in-memory CRUD to-do service built with FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()


# ---------------------------------------------------------------------------
# Override FastAPI's default 422 → return 400 with {"error": ...}
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Turn Pydantic / FastAPI 422 errors into 400 with an 'error' key."""
    messages = "; ".join(
        f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()
    )
    return JSONResponse(status_code=400, content={"error": messages})


# ---------------------------------------------------------------------------
# In-memory task store
# ---------------------------------------------------------------------------
SEED_TASKS: list[dict] = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Walk the dog", "done": False},
]

tasks: list[dict] = [t.copy() for t in SEED_TASKS]


def _next_id() -> int:
    """Return the next available task id."""
    return max((t["id"] for t in tasks), default=0) + 1


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


@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    """Create a new task from {"title": "..."}. Returns 201 on success."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Request body must be valid JSON"},
        )

    if not isinstance(body, dict) or "title" not in body:
        return JSONResponse(
            status_code=400,
            content={"error": "Field 'title' is required"},
        )

    title = body["title"]
    if not isinstance(title, str) or not title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Field 'title' must be a non-empty string"},
        )

    task = {"id": _next_id(), "title": title.strip(), "done": False}
    tasks.append(task)
    return JSONResponse(status_code=201, content=task)
