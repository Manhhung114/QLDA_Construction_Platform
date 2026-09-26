import os

from sqlalchemy import select

from . import models
from .database import SessionLocal
from .security import hash_password, verify_password


def sync_admin_password() -> None:
    """Keep the bootstrap admin password in sync with ADMIN_PASSWORD.

    The password itself is never logged or persisted in plaintext. The Railway
    environment variable is treated as the source of truth for the bootstrap
    administrator account and only a PBKDF2 hash is stored in PostgreSQL.
    """
    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        return

    db = SessionLocal()
    try:
        user = db.scalar(select(models.User).where(models.User.username == username))
        if user and not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
            user.role = "admin"
            user.is_active = True
            db.commit()
    finally:
        db.close()
