from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.auth import sessions
from app.config import settings
from app.db import get_db
from app.models import User


@dataclass
class CurrentUser:
    user: User
    is_admin: bool


def get_current_user(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> CurrentUser:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(401, "Not authenticated")
    found = sessions.lookup_session(db, token)
    if found is None:
        raise HTTPException(401, "Session expired")
    sess, user, allowed = found
    if allowed is None:
        sessions.revoke_session(db, token)
        raise HTTPException(403, "Access revoked")
    if sessions.refresh_if_stale(db, sess):
        sessions.set_cookie(response, token)
    return CurrentUser(user=user, is_admin=allowed.is_admin)


def require_admin(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not current.is_admin:
        raise HTTPException(403, "Admin only")
    return current
