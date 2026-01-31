from fastapi import FastAPI
from app.core.routes import router

app = FastAPI(title="Job Tracker")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(router)
