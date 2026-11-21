import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import sessions
from app.auth.deps import CurrentUser, get_current_user
from app.auth.oauth import oauth
from app.config import settings
from app.db import get_db
from app.models import AllowedEmail, User

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _frontend_redirect(error: str | None = None) -> RedirectResponse:
    url = settings.frontend_url
    if error:
        url += ("&" if "?" in url else "?") + urlencode({"auth_error": error})
    return RedirectResponse(url, status_code=303)


@router.get("/login")
async def login(request: Request):
    redirect_uri = settings.google_redirect_uri or str(request.url_for("auth_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="auth_callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        log.exception("OAuth token exchange failed")
        return _frontend_redirect("oauth_failed")

    info = token.get("userinfo") or {}
    email = (info.get("email") or "").lower()
    if not email or not info.get("email_verified"):
        return _frontend_redirect("email_not_verified")

    if db.get(AllowedEmail, email) is None:
        return _frontend_redirect("not_allowed")

    user = db.scalar(select(User).where(User.google_sub == info["sub"]))
    if user is None:
        user = User(google_sub=info["sub"], email=email)
        db.add(user)
    user.email = email
    user.name = info.get("name")
    user.picture_url = info.get("picture")
    user.last_login_at = func.now()
    db.commit()

    sessions.purge_expired(db)
    raw = sessions.create_session(db, user, request.headers.get("user-agent"))
    response = _frontend_redirect()
    sessions.set_cookie(response, raw)
    return response


@router.post("/logout", status_code=204)
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        sessions.revoke_session(db, token)
    response = Response(status_code=204)
    sessions.clear_cookie(response)
    return response


class MeResponse(BaseModel):
    email: str
    name: str | None
    picture_url: str | None
    is_admin: bool


@router.get("/me", response_model=MeResponse)
def me(current: CurrentUser = Depends(get_current_user)):
    u = current.user
    return MeResponse(
        email=u.email, name=u.name, picture_url=u.picture_url, is_admin=current.is_admin
    )
