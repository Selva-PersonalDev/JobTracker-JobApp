from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

from app.core.db import SessionLocal, engine
from app.core.models import Base, Job, User
from app.core.auth import hash_password, verify_password, get_current_user

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

# ---------- AUTH ----------

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
def register(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.close()
    return RedirectResponse("/login", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/forgot-password")
def forgot_password(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})


# ---------- DASHBOARD ----------

@router.get("/")
def home(request: Request):
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    db = SessionLocal()
    jobs = db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).all()
