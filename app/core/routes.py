from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

from app.core.db import SessionLocal, engine
from app.core.models import Base, Job, User
from app.core.auth import hash_password, verify_password, get_current_user

# Ensure tables exist
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
    "Joined",
]

# ---------------- AUTH ----------------

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
    finally:
        db.close()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password"
            }
        )

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@router.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...)):
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Username already exists. Please choose another."
                }
            )

        user = User(
            username=username,
            password_hash=hash_password(password)
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    return RedirectResponse("/login", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/forgot-password")
def forgot_password(request: Request):
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request}
    )

# ---------------- DASHBOARD ----------------

@router.get("/")
def home(request: Request):
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    db: Session = SessionLocal()
    try:
        jobs = (
            db.query(Job)
            .filter(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
            .all()
        )
    finally:
        db.close()

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
    request: Request,
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
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    db: Session = SessionLocal()
    try:
        job = Job(
            user_id=user_id,
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
    finally:
        db.close()

    return RedirectResponse("/", status_code=303)


@router.post("/update-status/{job_id}")
def update_status(request: Request, job_id: int, status: str = Form(...)):
    user_id = get_current_user(request)
    db: Session = SessionLocal()
    try:
        job = (
            db.query(Job)
            .filter(Job.id == job_id, Job.user_id == user_id)
            .first()
        )
        if job:
            job.status = status
            db.commit()
    finally:
        db.close()

    return RedirectResponse("/", status_code=303)


@router.post("/delete/{job_id}")
def delete_job(request: Request, job_id: int):
    user_id = get_current_user(request)
    db: Session = SessionLocal()
    try:
        job = (
            db.query(Job)
            .filter(Job.id == job_id, Job.user_id == user_id)
            .first()
        )
        if job:
            db.delete(job)
            db.commit()
    finally:
        db.close()

    return RedirectResponse("/", status_code=303)


@router.get("/job/{job_id}")
def job_detail(request: Request, job_id: int):
    user_id = get_current_user(request)
    db: Session = SessionLocal()
    try:
        job = (
            db.query(Job)
            .filter(Job.id == job_id, Job.user_id == user_id)
            .first()
        )
    finally:
        db.close()

    if not job:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job
        }
    )
