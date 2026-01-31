from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from app.core.db import SessionLocal, engine
from app.core.models import Base, Job
from fastapi.templating import Jinja2Templates

Base.metadata.create_all(bind=engine)

router = APIRouter()
templates = Jinja2Templates(directory="app/core/templates")

@router.get("/")
def home(request: Request):
    db: Session = SessionLocal()
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jobs": jobs}
    )

@router.post("/add")
def add_job(
    company: str = Form(...),
    role: str = Form(...),
    location: str = Form(None),
    job_url: str = Form(None),
    source: str = Form(None),
    ctc_budget: str = Form(None),
    applied_date: str = Form(None),
    status: str = Form(None),
    comments: str = Form(None),
):
    db: Session = SessionLocal()
    job = Job(
        company=company,
        role=role,
        location=location,
        job_url=job_url,
        source=source,
        ctc_budget=ctc_budget,
        applied_date=date.fromisoformat(applied_date) if applied_date else None,
        status=status,
        comments=comments,
    )
    db.add(job)
    db.commit()
    return RedirectResponse("/", status_code=303)
