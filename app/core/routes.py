import os
import shutil
from datetime import date

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, engine
from app.core.models import Base, Job, User
from app.core.auth import hash_password, verify_password, get_current_user
from app.core.storage import (
    upload_db_to_gcs,
    upload_jd_to_gcs,
    download_jd_from_gcs,
)

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
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
        )

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    db = SessionLocal()

    if db.query(User).filter(User.username == username).first():
        db.close()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already exists"},
        )

    user = User(
        username=username,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.close()

    upload_db_to_gcs()
    return RedirectResponse("/login", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

# ---------------- DASHBOARD ----------------

@router.get("/")
def home(request: Request):
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()
    jobs = (
        db.query(Job)
        .filter(Job.user_id == user_id)
        .order_by(Job.created_at.desc())
        .all()
    )
    db.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "jobs": jobs,
            "statuses": STATUS_OPTIONS,
        },
    )

# ---------------- ADD JOB ----------------

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
    job_description: str = Form(None),
    comments: str = Form(None),
    jd_file: UploadFile = File(None),
):
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    jd_filename = None

    if jd_file and jd_file.filename:
        temp_path = f"/tmp/{jd_file.filename}"
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(jd_file.file, f)

        upload_jd_to_gcs(temp_path, jd_file.filename)
        jd_filename = jd_file.filename

    db = SessionLocal()
    job = Job(
        user_id=user_id,
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
        job_description=job_description,
        jd_filename=jd_filename,
        comments=comments,
    )

    db.add(job)
    db.commit()
    db.close()

    upload_db_to_gcs()
    return RedirectResponse("/", status_code=303)

# ---------------- UPDATE STATUS ----------------

@router.post("/update-status/{job_id}")
def update_status(
    request: Request,
    job_id: int,
    status: str = Form(...),
):
    user_id = get_current_user(request)
    db = SessionLocal()

    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == user_id)
        .first()
    )
    if job:
        job.status = status
        db.commit()

    db.close()
    upload_db_to_gcs()
    return RedirectResponse("/", status_code=303)

# ---------------- DELETE JOB ----------------

@router.post("/delete/{job_id}")
def delete_job(request: Request, job_id: int):
    user_id = get_current_user(request)
    db = SessionLocal()

    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == user_id)
        .first()
    )
    if job:
        db.delete(job)
        db.commit()

    db.close()
    upload_db_to_gcs()
    return RedirectResponse("/", status_code=303)

# ---------------- EDIT JOB ----------------

@router.get("/job/{job_id}/edit")
def edit_job_page(request: Request, job_id: int):
    user_id = get_current_user(request)
    db = SessionLocal()

    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == user_id)
        .first()
    )
    db.close()

    if not job:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "edit_job.html",
        {
            "request": request,
            "job": job,
            "statuses": STATUS_OPTIONS,
        },
    )


@router.post("/job/{job_id}/edit")
def update_job(
    request: Request,
    job_id: int,
    company: str = Form(...),
    role: str = Form(...),
    location: str = Form(None),
    job_url: str = Form(None),
    source: str = Form(None),
    ctc_budget: str = Form(None),
    applied_date: str = Form(None),
    status: str = Form(...),
    job_description: str = Form(None),
    comments: str = Form(None),
    jd_file: UploadFile = File(None),
):
    user_id = get_current_user(request)
    db = SessionLocal()

    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == user_id)
        .first()
    )

    if not job:
        db.close()
        return RedirectResponse("/", status_code=303)

    job.company = company
    job.role = role
    job.location = location
    job.job_url = job_url
    job.source = source
    job.ctc_budget = ctc_budget
    job.applied_date = (
        date.fromisoformat(applied_date)
        if applied_date
        else None
    )
    job.status = status
    job.job_description = job_description
    job.comments = comments

    if jd_file and jd_file.filename:
        temp_path = f"/tmp/{jd_file.filename}"
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(jd_file.file, f)

        upload_jd_to_gcs(temp_path, jd_file.filename)
        job.jd_filename = jd_file.filename

    db.commit()
    db.close()

    upload_db_to_gcs()
    return RedirectResponse("/", status_code=303)

# ---------------- JOB DETAILS ----------------

@router.get("/job/{job_id}")
def job_detail(request: Request, job_id: int):
    user_id = get_current_user(request)
    db = SessionLocal()

    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == user_id)
        .first()
    )
    db.close()

    if not job:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": job},
    )

# ---------------- JD DOWNLOAD ----------------

@router.get("/jd/{filename}")
def download_jd(filename: str):
    local_path = f"/tmp/{filename}"
    download_jd_from_gcs(filename, local_path)
    return FileResponse(local_path, filename=filename)
