"""Task API – a simple in-memory CRUD to-do service built with FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title="Task API",
    description="A lightweight in-memory CRUD to-do service.",
    version="1.0",
)


# ---------------------------------------------------------------------------
# Override FastAPI's default 422 -> return 400 with {"error": ...}
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


# -- Error response models for docs ----------------------------------------
_404 = {"description": "Task not found", "content": {"application/json": {"example": {"error": "Task 99 not found"}}}}
_400 = {"description": "Validation error", "content": {"application/json": {"example": {"error": "Field 'title' is required"}}}}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/",
    summary="API root",
    description="Return API name, version, and available endpoint prefixes.",
    responses={200: {"description": "API metadata"}},
)
def root():
    """Return API metadata."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get(
    "/health",
    summary="Health check",
    description="Returns {\"status\": \"ok\"} when the service is running.",
    responses={200: {"description": "Service is healthy"}},
)
def health():
    """Health-check endpoint."""
    return {"status": "ok"}


@app.get(
    "/tasks",
    summary="List all tasks",
    description="Return every task currently stored in memory.",
    responses={200: {"description": "A JSON array of task objects"}},
)
def list_tasks(
    done: bool | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0
):
    """Return every task in the store, with optional filtering and pagination."""
    result = tasks
    if done is not None:
        result = [t for t in result if t["done"] == done]
    if search:
        search_lower = search.lower()
        result = [t for t in result if search_lower in t["title"].lower()]
    return result[offset:offset + limit]


@app.get(
    "/stats",
    summary="Get task statistics",
    description="Returns the total number of tasks, completed tasks, and open tasks.",
    responses={200: {"description": "Task statistics object"}},
)
def get_stats():
    """Return task statistics."""
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    return {"total": total, "done": done_count, "open": total - done_count}


@app.post(
    "/reset",
    summary="Reset tasks",
    description="Restores the tasks list to the initial seed state.",
    responses={200: {"description": "Tasks reset successfully"}},
)
def reset_tasks():
    """Restores the tasks list to the initial seed state."""
    tasks.clear()
    tasks.extend([t.copy() for t in SEED_TASKS])
    return {"message": "Tasks reset to initial state"}


@app.get(
    "/tasks/{task_id}",
    summary="Get a task",
    description="Return a single task by its numeric id.",
    responses={200: {"description": "The requested task"}, 404: _404},
)
def get_task(task_id: int):
    """Return a single task by its id, or 404."""
    task = _find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )
    return task


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description='Accept {"title": "..."}, assign the next free id, set done=false, and return the new task.',
    responses={201: {"description": "Task created"}, 400: _400},
)
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


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Update title and/or done for an existing task.",
    responses={200: {"description": "Updated task"}, 400: _400, 404: _404},
)
async def update_task(task_id: int, request: Request):
    """Update title and/or done for a task. Returns the updated task."""
    task = _find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Request body must be valid JSON"},
        )

    if not isinstance(body, dict) or not body:
        return JSONResponse(
            status_code=400,
            content={"error": "Request body must be a non-empty JSON object"},
        )

    # Validate fields
    allowed = {"title", "done"}
    unknown = set(body.keys()) - allowed
    if unknown:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unknown fields: {', '.join(sorted(unknown))}"},
        )

    if "title" in body:
        title = body["title"]
        if not isinstance(title, str) or not title.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Field 'title' must be a non-empty string"},
            )
        task["title"] = title.strip()

    if "done" in body:
        done = body["done"]
        if not isinstance(done, bool):
            return JSONResponse(
                status_code=400,
                content={"error": "Field 'done' must be a boolean"},
            )
        task["done"] = done

    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Remove a task by id. Returns 204 with an empty body on success.",
    responses={204: {"description": "Task deleted (no body)"}, 404: _404},
)
def delete_task(task_id: int):
    """Delete a task by id. Returns 204 with no body."""
    task = _find_task(task_id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task {task_id} not found"},
        )
    tasks.remove(task)
    return Response(status_code=204)
