from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.db import SessionLocal, engine
from app.core.models import Base, Job
from fastapi.templating import Jinja2Templates

Base.metadata.create_all(bind=engine)

router = APIRouter()
templates = Jinja2Templates(directory="app/core/templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    db: Session = SessionLocal()
    jobs = db.query(Job).all()
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs})

@router.post("/add")
def add_job(
    company: str = Form(...),
    role: str = Form(...),
    status: str = Form(...)
):
    db: Session = SessionLocal()
    job = Job(company=company, role=role, status=status)
    db.add(job)
    db.commit()
    return RedirectResponse("/", status_code=303)
