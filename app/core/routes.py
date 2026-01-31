import io
import os
import shutil
from datetime import date

import pandas as pd
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.core.db import SessionLocal, engine
from app.core.models import Base, Job, User
from app.core.auth import hash_password, verify_password, get_current_user

Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "/data/jd_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    if db.query(User).filter(User.username == username).first():
        db.close()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already exists"}
        )

    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.close()
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
    job_description: str = Form(None),
    comments: str = Form(None),
    jd_file: UploadFile = File(None),
):
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    filename = None
    if jd_file and jd_file.filename:
        filename = f"{user_id}_{jd_file.filename}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            shutil.copyfileobj(jd_file.file, f)

    db = SessionLocal()
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
        job_description=job_description,
        jd_filename=filename,
        comments=comments,
    )
    db.add(job)
    db.commit()
    db.close()

    return RedirectResponse("/", status_code=303)


@router.post("/update-status/{job_id}")
def update_status(request: Request, job_id: int, status: str = Form(...)):
    user_id = get_current_user(request)
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    if job:
        job.status = status
        db.commit()
    db.close()
    return RedirectResponse("/", status_code=303)


@router.post("/delete/{job_id}")
def delete_job(request: Request, job_id: int):
    user_id = get_current_user(request)
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    if job:
        db.delete(job)
        db.commit()
    db.close()
    return RedirectResponse("/", status_code=303)


@router.get("/job/{job_id}")
def job_detail(request: Request, job_id: int):
    user_id = get_current_user(request)
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    db.close()

    if not job:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": job}
    )


@router.get("/jd/{filename}")
def download_jd(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename), filename=filename)

# ---------------- EXPORT ----------------

@router.get("/export/xlsx")
def export_xlsx(request: Request):
    user_id = get_current_user(request)
    db = SessionLocal()
    jobs = db.query(Job).filter(Job.user_id == user_id).all()
    db.close()

    data = [{
        "Company": j.company,
        "Role": j.role,
        "Location": j.location,
        "Job URL": j.job_url,
        "Source": j.source,
        "CTC Budget": j.ctc_budget,
        "Applied Date": j.applied_date,
        "Status": j.status,
        "Job Description": j.job_description,
        "JD File": j.jd_filename,
        "Comments": j.comments,
    } for j in jobs]

    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=jobtracker.xlsx"}
    )


@router.get("/export/pdf")
def export_pdf(request: Request):
    user_id = get_current_user(request)
    db = SessionLocal()
    jobs = db.query(Job).filter(Job.user_id == user_id).all()
    db.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    y = 800

    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Job Applications")
    y -= 30
    p.setFont("Helvetica", 10)

    for j in jobs:
        p.drawString(40, y, f"{j.company} | {j.role} | {j.status} | {j.applied_date}")
        y -= 14
        if y < 40:
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=jobtracker.pdf"}
    )
