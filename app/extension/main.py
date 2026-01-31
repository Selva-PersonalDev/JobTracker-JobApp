from fastapi import FastAPI

app = FastAPI(title="Extension Service")

@app.get("/health")
def health():
    return {"status": "ok"}
