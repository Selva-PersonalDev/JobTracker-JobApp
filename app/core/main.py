from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.core.routes import router

app = FastAPI(title="Job Tracker")

app.add_middleware(
    SessionMiddleware,
    secret_key="dev-secret-change-later"
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(router)
