import os
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.core.routes import router

app = FastAPI(title="Job Tracker")

# Session middleware (stable across restarts)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "unsafe-dev-secret"),
)

@app.get("/health")
def health():
    return {"status": "ok"}

# Register routes
app.include_router(router)
