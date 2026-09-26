import json
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from . import models, models_extra
from .database import SessionLocal
from .security import decode_access_token
from .v2 import permit

NESTED = {"project-members", "checklists", "document-revisions"}


def _bearer_user(request: Request, db):
    value = request.headers.get("authorization", "")
    if not value.lower().startswith("bearer "):
        return None
    payload = decode_access_token(value.split(" ", 1)[1].strip())
    if not payload:
        return None
    try:
        return db.get(models.User, int(payload["sub"]))
    except Exception:
        return None


async def _json_body(request: Request) -> dict[str, Any]:
    body = await request.body()
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    request._receive = receive
    if not body:
        return {}
    try:
        return json.loads(body)
    except Exception:
        return {}


def _project_from_nested(db, module: str, record_id: int | None = None, payload: dict[str, Any] | None = None):
    payload = payload or {}
    if module == "project-members":
        if record_id:
            row = db.get(models_extra.ProjectMember, record_id)
            return row.project_id if row else None
        value = payload.get("project_id")
        return int(value) if value not in (None, "") else None
    if module == "checklists":
        task_id = payload.get("task_id")
        if record_id and not task_id:
            row = db.get(models_extra.ChecklistItem, record_id)
            task_id = row.task_id if row else None
        task = db.get(models.Task, int(task_id)) if task_id else None
        return task.project_id if task else None
    if module == "document-revisions":
        document_id = payload.get("document_id")
        if record_id and not document_id:
            row = db.get(models.DocumentRevision, record_id)
            document_id = row.document_id if row else None
        doc = db.get(models.Document, int(document_id)) if document_id else None
        return doc.project_id if doc else None
    return None


def install_nested_rbac_guard(app):
    @app.middleware("http")
    async def nested_rbac_guard(request: Request, call_next):
        path = request.url.path.rstrip("/")
        db = SessionLocal()
        try:
            user = _bearer_user(request, db)
            if not user or user.role in {"admin", "manager"}:
                return await call_next(request)

            if path.startswith("/api/data/audit-logs"):
                return JSONResponse({"detail": "Audit log requires admin/manager permission"}, status_code=403)

            if path.startswith("/api/export/"):
                export_name = path.rsplit("/", 1)[-1].removesuffix(".csv")
                if export_name in NESTED or export_name == "audit-logs":
                    return JSONResponse({"detail": "Scoped export is not available for this protected dataset"}, status_code=403)

            parts = path.split("/")
            if len(parts) < 4 or parts[1:3] != ["api", "data"]:
                return await call_next(request)
            module = parts[3]
            if module not in NESTED:
                return await call_next(request)

            record_id = None
            if len(parts) >= 5:
                try:
                    record_id = int(parts[4])
                except ValueError:
                    pass
            payload = await _json_body(request) if request.method in {"POST", "PATCH", "PUT"} else {}
            project_id = _project_from_nested(db, module, record_id, payload)
            if project_id is None and request.method == "GET" and record_id is None:
                return JSONResponse({"detail": "Use /api/scoped/{module}?project_id=... for nested data"}, status_code=400)
            if project_id is None:
                return JSONResponse({"detail": "Cannot resolve project for nested record"}, status_code=400)

            action = "read"
            if request.method in {"POST", "PATCH", "PUT"}:
                action = "manage_members" if module == "project-members" else "write"
            elif request.method == "DELETE":
                action = "manage_members" if module == "project-members" else "delete"
            try:
                permit(db, user, action, project_id, module)
            except HTTPException as exc:
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
            return await call_next(request)
        finally:
            db.close()
