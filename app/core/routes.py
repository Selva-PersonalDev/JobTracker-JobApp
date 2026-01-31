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

STATUS_OPTIONS = [
    "Applied",
    "Screening Completed",
    "Interview 1 Scheduled",
    "Interview 2 Scheduled",
    "Final Interview Scheduled",
    "Verbal Offer",
    "Offer Released",
    "Offer Accepted",
    "Joined"
]

@router.get("/")
def home(request: Request):
    db: Session = SessionLocal()
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,
            "statuses": STATUS_OPTIONS
        }
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
    status: str = Form(...),
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

@router.post("/delete/{job_id}")
def delete_job(job_id: int):
    db: Session = SessionLocal()
    job = db.query(Job).get(job_id)
    if job:
        db.delete(job)
        db.commit()
    return RedirectResponse("/", status_code=303)
