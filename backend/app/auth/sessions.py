import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AllowedEmail, AuthSession, User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _ttl() -> timedelta:
    return timedelta(days=settings.session_ttl_days)


def create_session(db: Session, user: User, user_agent: str | None) -> str:
    """Create a session row and return the raw token (only its hash is stored)."""
    token = secrets.token_urlsafe(32)
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=_hash(token),
            expires_at=_now() + _ttl(),
            user_agent=(user_agent or "")[:512] or None,
        )
    )
    db.commit()
    return token


def lookup_session(
    db: Session, token: str
) -> tuple[AuthSession, User, AllowedEmail | None] | None:
    """Return (session, user, allow-list entry) for a valid token, else None.

    The allow-list entry is re-checked on every call, so removing an email from the
    list takes effect immediately.
    """
    row = db.execute(
        select(AuthSession, User, AllowedEmail)
        .join(User, User.id == AuthSession.user_id)
        .outerjoin(AllowedEmail, AllowedEmail.email == User.email)
        .where(AuthSession.token_hash == _hash(token))
    ).first()
    if row is None:
        return None
    sess, user, allowed = row
    if sess.expires_at <= _now():
        db.delete(sess)
        db.commit()
        return None
    return sess, user, allowed


def refresh_if_stale(db: Session, sess: AuthSession) -> bool:
    """Sliding expiration: extend when more than a day has elapsed since the last extension."""
    new_expiry = _now() + _ttl()
    if new_expiry - sess.expires_at > timedelta(days=1):
        sess.expires_at = new_expiry
        db.commit()
        return True
    return False


def revoke_session(db: Session, token: str) -> None:
    db.execute(delete(AuthSession).where(AuthSession.token_hash == _hash(token)))
    db.commit()


def purge_expired(db: Session) -> None:
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= _now()))
    db.commit()


def set_cookie(response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=int(_ttl().total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_cookie(response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")
