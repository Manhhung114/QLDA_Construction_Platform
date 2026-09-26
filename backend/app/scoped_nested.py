from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, models_extra
from .database import get_db
from .v2 import as_dict, current_user, permit

router = APIRouter(prefix="/api/scoped", tags=["scoped-nested"])


@router.get("/{module}")
def scoped_nested_list(
    module: str,
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    permit(db, user, "read", project_id, module)
    if module == "project-members":
        rows = db.execute(
            select(models_extra.ProjectMember, models.User)
            .join(models.User, models.User.id == models_extra.ProjectMember.user_id)
            .where(models_extra.ProjectMember.project_id == project_id)
            .order_by(models_extra.ProjectMember.id)
        ).all()
        return [{**as_dict(m), "username": u.username, "full_name": u.full_name, "email": u.email} for m, u in rows]
    if module == "checklists":
        rows = db.scalars(
            select(models_extra.ChecklistItem)
            .join(models.Task, models.Task.id == models_extra.ChecklistItem.task_id)
            .where(models.Task.project_id == project_id)
            .order_by(models_extra.ChecklistItem.id)
        ).all()
        return [as_dict(r) for r in rows]
    if module == "document-revisions":
        rows = db.scalars(
            select(models.DocumentRevision)
            .join(models.Document, models.Document.id == models.DocumentRevision.document_id)
            .where(models.Document.project_id == project_id)
            .order_by(models.DocumentRevision.id.desc())
        ).all()
        return [as_dict(r) for r in rows]
    raise HTTPException(404, "Unknown nested module")
