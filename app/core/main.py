from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.core.routes import router
from app.core.storage import download_db_from_gcs

app = FastAPI(title="Job Tracker")

download_db_from_gcs()

app.add_middleware(SessionMiddleware, secret_key="jobtracker-secret")

@app.get("/health")
def health():
    return {"status": "ok"}
    
app.include_router(router)
