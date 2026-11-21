import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AllowedEmail

log = logging.getLogger(__name__)


def seed_admins(db: Session) -> None:
    """Bootstrap: make sure INITIAL_ADMIN_EMAILS exist in the allow-list as admins."""
    for raw in settings.initial_admin_emails.split(","):
        email = raw.strip().lower()
        if not email:
            continue
        row = db.get(AllowedEmail, email)
        if row is None:
            db.add(AllowedEmail(email=email, is_admin=True, added_by="seed"))
            log.info("seeded admin %s", email)
        elif not row.is_admin:
            row.is_admin = True
    db.commit()
