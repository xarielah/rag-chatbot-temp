from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import CurrentUser, require_admin
from app.db import get_db
from app.models import AllowedEmail

router = APIRouter(prefix="/api/admin/allowed-emails", tags=["admin"])


class AllowedEmailOut(BaseModel):
    email: str
    is_admin: bool
    added_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AllowedEmailIn(BaseModel):
    email: EmailStr
    is_admin: bool = False


class AllowedEmailPatch(BaseModel):
    is_admin: bool


@router.get("", response_model=list[AllowedEmailOut])
def list_allowed(db: Session = Depends(get_db), _: CurrentUser = Depends(require_admin)):
    return db.scalars(select(AllowedEmail).order_by(AllowedEmail.email)).all()


@router.post("", response_model=AllowedEmailOut, status_code=201)
def add_allowed(
    body: AllowedEmailIn,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    email = body.email.lower()
    if db.get(AllowedEmail, email):
        raise HTTPException(409, "Already in the list")
    row = AllowedEmail(email=email, is_admin=body.is_admin, added_by=admin.user.email)
    db.add(row)
    db.commit()
    return row


def _guard_self(admin: CurrentUser, email: str) -> None:
    if email == admin.user.email:
        raise HTTPException(400, "You can't modify your own access")


@router.patch("/{email}", response_model=AllowedEmailOut)
def update_allowed(
    email: str,
    body: AllowedEmailPatch,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    email = email.lower()
    _guard_self(admin, email)
    row = db.get(AllowedEmail, email)
    if row is None:
        raise HTTPException(404, "Not found")
    row.is_admin = body.is_admin
    db.commit()
    return row


@router.delete("/{email}", status_code=204)
def remove_allowed(
    email: str, db: Session = Depends(get_db), admin: CurrentUser = Depends(require_admin)
):
    email = email.lower()
    _guard_self(admin, email)
    row = db.get(AllowedEmail, email)
    if row is None:
        raise HTTPException(404, "Not found")
    db.delete(row)  # active sessions stop working on their next request
    db.commit()
