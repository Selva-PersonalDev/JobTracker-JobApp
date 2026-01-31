from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from fastapi.templating import Jinja2Templates

from app.core.db import SessionLocal, engine
from app.core.models import Base, Job

# Create tables (safe for SQLite)
Base.metadata.create_all(bind=engine)

router = APIRouter()
templates = Jinja2Templates(directory="app/core/templates")

# Centralized status options (single source of truth)
STATUS_OPTIONS = [
    "Applied",
    "Screening Completed",
    "Interview 1 Scheduled",
    "Interview 2 Scheduled",
    "Final Interview Scheduled",
    "Verbal Offer",
    "Offer Released",
    "Offer Accepted",
    "Joined",
]


# -----------------------------
# HOME / DASHBOARD
# -----------------------------
@router.get("/")
def home(request: Request):
    db: Session = SessionLocal()
    try:
        jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    finally:
        db.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,
            "statuses": STATUS_OPTIONS,
        },
    )


# -----------------------------
# ADD JOB
# -----------------------------
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
    try:
        job = Job(
            company=company,
            role=role,
            location=location,
            job_url=job_url,
            source=source,
            ctc_budget=ctc_budget,
            applied_date=date.fromisoformat(applied_date)
            if applied_date
            else None,
            status=status,
            comments=comments,
        )
        db.add(job)
        db.commit()
    finally:
        db.close()

    return RedirectResponse("/", status_code=303)


# -----------------------------
# UPDATE JOB STATUS (INLINE)
# -----------------------------
@router.post("/update-status/{job_id}")
def update_status(job_id: int, status: str = Form(...)):
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            db.commit()
    finally:
        db.close()

    return RedirectResponse("/", status_code=303)


# -----------------------------
# DELETE JOB
# -----------------------------
@router.post("/delete/{job_id}")
def delete_job(job_id: int):
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
    finally:
        db.close()

    return RedirectResponse("/", status_code=303)


# -----------------------------
# JOB DETAIL VIEW
# -----------------------------
@router.get("/job/{job_id}")
def job_detail(request: Request, job_id: int):
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
    finally:
        db.close()

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job,
        },
    )
