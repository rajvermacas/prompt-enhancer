from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import DuplicateEmailError
from app.dependencies import get_auth_service
from app.services.auth_service import InvalidCredentialsError

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

COOKIE_MAX_AGE = 604800  # 7 days


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service = get_auth_service()
        try:
            auth_service.validate_session(session_id)
            return RedirectResponse(url="/", status_code=303)
        except Exception:
            pass
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": None}
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    auth_service = get_auth_service()

    try:
        user = auth_service.authenticate_user(email, password)
    except InvalidCredentialsError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password"},
        )

    session = auth_service.create_session(user.id)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session.id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service = get_auth_service()
        try:
            auth_service.validate_session(session_id)
            return RedirectResponse(url="/", status_code=303)
        except Exception:
            pass
    return templates.TemplateResponse(
        "register.html", {"request": request, "error": None}
    )


@router.post("/register")
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    auth_service = get_auth_service()

    try:
        user = auth_service.register_user(email, password)
    except DuplicateEmailError:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email already registered"},
        )

    session = auth_service.create_session(user.id)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session.id,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout")
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service = get_auth_service()
        auth_service.logout(session_id)

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_id")
    return response
