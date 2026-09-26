import csv
import hashlib
import io
import json
import os
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, func, inspect, or_, select
from sqlalchemy.orm import Session

from . import models, models_extra
from .database import Base, SessionLocal, engine, get_db
from .security import create_access_token, decode_access_token, hash_password, verify_password

APP_NAME = "QLDA Construction Platform API"
APP_VERSION = "2.0.0"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=APP_NAME, version=APP_VERSION)
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
security = HTTPBearer(auto_error=False)

REGISTRY = {
    "projects": models.Project, "project-members": models_extra.ProjectMember,
    "wbs": models.WBSItem, "tasks": models.Task, "task-dependencies": models_extra.TaskDependency,
    "checklists": models_extra.ChecklistItem, "schedule": models.ScheduleActivity,
    "resources": models.Resource, "resource-assignments": models_extra.ResourceAssignment,
    "timesheets": models.Timesheet, "boq": models.BOQItem, "budget-versions": models_extra.BudgetVersion,
    "costs": models.CostEntry, "contracts": models.Contract, "payments": models_extra.PaymentCertificate,
    "procurement": models.ProcurementOrder, "documents": models.Document,
    "document-revisions": models.DocumentRevision, "transmittals": models_extra.Transmittal,
    "quality": models.QualityItem, "changes": models.ChangeOrder, "claims": models_extra.Claim,
    "comments": models.Comment, "notifications": models.Notification,
    "workflow-rules": models.WorkflowRule, "approval-actions": models_extra.ApprovalAction,
    "audit-logs": models.AuditLog,
}

LABELS = {
    "projects": "Project & Portfolio", "tasks": "Task & WBS", "schedule": "Schedule",
    "resources": "Resource & Time", "boq": "BOQ & Cost Control",
    "contracts": "Contract & Procurement", "documents": "Document Control",
    "quality": "Quality / RFI / NCR / INS", "changes": "Change Management",
    "comments": "Collaboration", "dashboard": "Dashboard & BI", "automation": "Automation & AI",
}

APPROVABLE = {"documents", "document-revisions", "quality", "changes", "claims", "contracts", "payments", "procurement", "budget-versions"}
WORKFLOW = {
    "documents": {"draft": ["submitted"], "submitted": ["under_review", "rejected"], "under_review": ["approved", "rejected"], "rejected": ["submitted"], "approved": ["closed"]},
    "document-revisions": {"submitted": ["under_review", "rejected"], "under_review": ["approved", "rejected"], "rejected": ["submitted"]},
    "quality": {"open": ["submitted", "closed"], "submitted": ["under_review", "rejected"], "under_review": ["approved", "rejected"], "rejected": ["submitted"], "approved": ["closed"]},
    "changes": {"draft": ["submitted"], "submitted": ["under_review", "rejected"], "under_review": ["approved", "rejected"], "rejected": ["submitted"], "approved": ["closed"]},
    "claims": {"draft": ["submitted"], "submitted": ["under_review", "rejected"], "under_review": ["approved", "rejected"], "rejected": ["submitted"], "approved": ["closed"]},
    "contracts": {"draft": ["active", "cancelled"], "active": ["expired", "closed", "cancelled"]},
    "payments": {"draft": ["submitted"], "submitted": ["under_review", "rejected"], "under_review": ["approved", "rejected"], "rejected": ["submitted"], "approved": ["paid"]},
    "procurement": {"requested": ["approved", "cancelled"], "approved": ["ordered"], "ordered": ["delivered", "cancelled"], "delivered": ["closed"]},
    "budget-versions": {"draft": ["submitted"], "submitted": ["approved", "rejected"], "rejected": ["draft"]},
}
ROLE_ACTIONS = {
    "owner": {"read", "write", "delete", "approve", "manage_members"},
    "project_admin": {"read", "write", "delete", "approve", "manage_members"},
    "manager": {"read", "write", "approve"}, "reviewer": {"read", "approve"},
    "member": {"read", "write"}, "contractor": {"read", "write"}, "guest": {"read"},
}


def init_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "")
        if not password:
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise RuntimeError("ADMIN_PASSWORD must be set in production")
            password = "ChangeMe123!"
        existing = db.scalar(select(models.User).where(models.User.username == username))
        if not existing:
            db.add(models.User(username=username, email=os.getenv("ADMIN_EMAIL") or None, full_name="System Administrator", role="admin", password_hash=hash_password(password)))
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def startup_event(): init_database()


def as_dict(obj: Any):
    out = {}
    for c in inspect(obj.__class__).columns:
        v = getattr(obj, c.key)
        if isinstance(v, Decimal): v = float(v)
        elif isinstance(v, (date, datetime)): v = v.isoformat()
        out[c.key] = v
    return out


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)):
    if not credentials: raise HTTPException(401, "Authentication required")
    payload = decode_access_token(credentials.credentials)
    if not payload: raise HTTPException(401, "Invalid or expired token")
    user = db.get(models.User, int(payload["sub"]))
    if not user or not user.is_active: raise HTTPException(401, "User is inactive or not found")
    return user


def admin_user(user: models.User = Depends(current_user)):
    if user.role != "admin": raise HTTPException(403, "Admin permission required")
    return user


def model_for(module: str):
    model = REGISTRY.get(module)
    if not model: raise HTTPException(404, f"Unknown module: {module}")
    return model


def writable(model): return {c.name: c for c in inspect(model).columns if c.name not in {"id", "created_at", "updated_at"}}


def coerce(column, value):
    if value in ("", None): return None if column.nullable else value
    if isinstance(column.type, DateTime): return datetime.fromisoformat(value) if isinstance(value, str) else value
    if isinstance(column.type, Date): return date.fromisoformat(value) if isinstance(value, str) else value
    if isinstance(column.type, Integer): return int(value)
    if isinstance(column.type, Numeric): return Decimal(str(value))
    if isinstance(column.type, Boolean): return value.lower() in {"1", "true", "yes", "on"} if isinstance(value, str) else bool(value)
    return value


def clean(model, payload):
    allowed = writable(model)
    return {k: coerce(allowed[k], v) for k, v in payload.items() if k in allowed}


def project_id_for(module, row=None, payload=None, db=None):
    if payload and payload.get("project_id") not in (None, ""): return int(payload["project_id"])
    if row is not None and hasattr(row, "project_id"): return row.project_id
    if module == "projects" and row is not None: return row.id
    if module == "document-revisions" and row is not None and db:
        doc = db.get(models.Document, row.document_id); return doc.project_id if doc else None
    if module == "checklists" and row is not None and db:
        task = db.get(models.Task, row.task_id); return task.project_id if task else None
    return None


def role_for(db, user, project_id):
    if user.role == "admin": return "owner"
    if user.role == "manager": return "manager"
    if project_id is None: return None
    m = db.scalar(select(models_extra.ProjectMember).where(models_extra.ProjectMember.project_id == project_id, models_extra.ProjectMember.user_id == user.id))
    return m.role if m else None


def permit(db, user, action, project_id, module):
    if user.role == "admin" or (user.role == "manager" and action != "manage_members"): return
    role = role_for(db, user, project_id)
    if not role or action not in ROLE_ACTIONS.get(role, set()): raise HTTPException(403, f"Permission denied: {action} on {module}")


def scoped(stmt, model, user, db, project_id=None):
    if project_id is not None and hasattr(model, "project_id"): stmt = stmt.where(model.project_id == project_id)
    if user.role not in {"admin", "manager"}:
        allowed = select(models_extra.ProjectMember.project_id).where(models_extra.ProjectMember.user_id == user.id)
        if model is models.Project: stmt = stmt.where(models.Project.id.in_(allowed))
        elif hasattr(model, "project_id"): stmt = stmt.where(model.project_id.in_(allowed))
    return stmt


def audit(db, user, module, entity_id, action, before=None, after=None, request=None):
    db.add(models.AuditLog(user_id=user.id if user else None, entity_type=module, entity_id=entity_id, action=action,
        before_json=json.dumps(before, ensure_ascii=False, default=str) if before else None,
        after_json=json.dumps(after, ensure_ascii=False, default=str) if after else None))
    db.commit()


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1)); return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(select(1)); return {"ready": True}


@app.post("/api/auth/login")
def login(payload: dict[str, Any], db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.username == str(payload.get("username", "")).strip()))
    if not user or not verify_password(str(payload.get("password", "")), user.password_hash): raise HTTPException(401, "Sai tài khoản hoặc mật khẩu")
    if not user.is_active: raise HTTPException(403, "Tài khoản đã bị khóa")
    return {"access_token": create_access_token(user.id, user.username, user.role), "token_type": "bearer", "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role}}


@app.get("/api/auth/me")
def me(user=Depends(current_user)): return {"id": user.id, "username": user.username, "email": user.email, "full_name": user.full_name, "role": user.role}


@app.get("/api/auth/users")
def users(db: Session = Depends(get_db), _=Depends(admin_user)):
    return [{"id": u.id, "username": u.username, "email": u.email, "full_name": u.full_name, "role": u.role, "is_active": u.is_active} for u in db.scalars(select(models.User).order_by(models.User.username)).all()]


@app.post("/api/auth/users")
def create_user(payload: dict[str, Any], db: Session = Depends(get_db), _=Depends(admin_user)):
    username, password = str(payload.get("username", "")).strip(), str(payload.get("password", ""))
    if not username or len(password) < 10: raise HTTPException(400, "Username required; password must have at least 10 characters")
    if db.scalar(select(models.User).where(models.User.username == username)): raise HTTPException(409, "Username already exists")
    role = payload.get("role") or "member"
    if role not in {"admin", "manager", "member", "guest"}: raise HTTPException(400, "Invalid role")
    u = models.User(username=username, email=payload.get("email") or None, full_name=payload.get("full_name") or username, role=role, password_hash=hash_password(password))
    db.add(u); db.commit(); db.refresh(u); return {"id": u.id, "username": u.username, "role": u.role}


@app.get("/api/modules")
def modules(_=Depends(current_user)): return [{"slug": k, "label": v} for k, v in LABELS.items()]


@app.post("/api/files/upload")
async def upload(file: UploadFile = File(...), user=Depends(current_user)):
    original = Path(file.filename or "upload.bin").name; ext = Path(original).suffix.lower()
    allowed = {x.strip().lower() for x in os.getenv("ALLOWED_UPLOAD_EXTENSIONS", ".pdf,.xlsx,.xls,.csv,.doc,.docx,.jpg,.jpeg,.png,.dwg,.zip").split(",") if x.strip()}
    if ext not in allowed: raise HTTPException(415, f"File type {ext or '(none)'} is not allowed")
    content = await file.read(); max_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
    if len(content) > max_mb * 1024 * 1024: raise HTTPException(413, f"File exceeds {max_mb} MB")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", original)[:180]
    target = UPLOAD_DIR / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{safe}"; target.write_bytes(content)
    return {"filename": original, "size": len(content), "sha256": hashlib.sha256(content).hexdigest(), "stored_by": user.username, "url": f"/uploads/{target.name}"}


@app.get("/api/data/{module}")
def list_data(module: str, project_id: int | None = None, q: str | None = None, status: str | None = None, limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user=Depends(current_user)):
    model = model_for(module); stmt = scoped(select(model), model, user, db, project_id)
    if status and hasattr(model, "status"): stmt = stmt.where(model.status == status)
    if q:
        cols = [c for c in inspect(model).columns if isinstance(c.type, (String, Text))]
        if cols: stmt = stmt.where(or_(*[c.ilike(f"%{q}%") for c in cols]))
    return [as_dict(r) for r in db.scalars(stmt.order_by(model.id.desc()).limit(limit).offset(offset)).all()]


@app.get("/api/data/{module}/{record_id}")
def get_data(module: str, record_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    model = model_for(module); row = db.get(model, record_id)
    if not row: raise HTTPException(404, "Record not found")
    permit(db, user, "read", project_id_for(module, row, db=db), module); return as_dict(row)


@app.post("/api/data/{module}")
def create_data(module: str, payload: dict[str, Any], request: Request, db: Session = Depends(get_db), user=Depends(current_user)):
    if module in {"audit-logs", "approval-actions"}: raise HTTPException(403, "System records are immutable")
    model = model_for(module); data = clean(model, payload); pid = project_id_for(module, payload=payload)
    if module == "projects":
        if user.role not in {"admin", "manager"}: raise HTTPException(403, "Only admin/manager can create projects")
    else: permit(db, user, "write", pid, module)
    if module == "contracts" and data.get("start_date") and data.get("duration_days") and not data.get("end_date"): data["end_date"] = data["start_date"] + timedelta(days=int(data["duration_days"]))
    if module == "comments": data["author"] = user.full_name or user.username
    row = model(**data); db.add(row)
    try: db.commit(); db.refresh(row)
    except Exception as exc: db.rollback(); raise HTTPException(400, f"Cannot create record: {exc.__class__.__name__}") from exc
    if module == "projects": db.add(models_extra.ProjectMember(project_id=row.id, user_id=user.id, role="owner", can_approve=True)); db.commit()
    audit(db, user, module, row.id, "create", after=as_dict(row), request=request); return as_dict(row)


@app.patch("/api/data/{module}/{record_id}")
def update_data(module: str, record_id: int, payload: dict[str, Any], request: Request, db: Session = Depends(get_db), user=Depends(current_user)):
    if module in {"audit-logs", "approval-actions"}: raise HTTPException(403, "System records are immutable")
    model = model_for(module); row = db.get(model, record_id)
    if not row: raise HTTPException(404, "Record not found")
    permit(db, user, "write", project_id_for(module, row, payload, db), module); before = as_dict(row); data = clean(model, payload)
    if "status" in data and module in APPROVABLE and data["status"] != getattr(row, "status", None): raise HTTPException(409, "Use workflow transition for approval status")
    for k, v in data.items(): setattr(row, k, v)
    if module == "contracts" and row.start_date and row.duration_days and "end_date" not in data: row.end_date = row.start_date + timedelta(days=int(row.duration_days))
    db.commit(); db.refresh(row); audit(db, user, module, row.id, "update", before, as_dict(row), request); return as_dict(row)


@app.delete("/api/data/{module}/{record_id}")
def delete_data(module: str, record_id: int, request: Request, db: Session = Depends(get_db), user=Depends(current_user)):
    if module in {"audit-logs", "approval-actions"}: raise HTTPException(403, "System records are immutable")
    model = model_for(module); row = db.get(model, record_id)
    if not row: raise HTTPException(404, "Record not found")
    permit(db, user, "delete", project_id_for(module, row, db=db), module); before = as_dict(row); db.delete(row)
    try: db.commit()
    except Exception as exc: db.rollback(); raise HTTPException(409, "Record is referenced by other data") from exc
    audit(db, user, module, record_id, "delete", before, None, request); return {"deleted": True, "id": record_id}


@app.post("/api/projects/{project_id}/members")
def add_member(project_id: int, payload: dict[str, Any], db: Session = Depends(get_db), user=Depends(current_user)):
    permit(db, user, "manage_members", project_id, "project-members")
    row = models_extra.ProjectMember(project_id=project_id, user_id=int(payload["user_id"]), role=payload.get("role", "member"), can_approve=bool(payload.get("can_approve", False)))
    db.add(row)
    try: db.commit(); db.refresh(row)
    except Exception as exc: db.rollback(); raise HTTPException(409, "User is already assigned to project") from exc
    return as_dict(row)


@app.get("/api/projects/{project_id}/members")
def members(project_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    permit(db, user, "read", project_id, "project-members")
    rows = db.execute(select(models_extra.ProjectMember, models.User).join(models.User, models.User.id == models_extra.ProjectMember.user_id).where(models_extra.ProjectMember.project_id == project_id)).all()
    return [{**as_dict(m), "username": u.username, "full_name": u.full_name, "email": u.email} for m, u in rows]


@app.post("/api/workflow/transition")
def transition(payload: dict[str, Any], request: Request, db: Session = Depends(get_db), user=Depends(current_user)):
    module = str(payload.get("module", "")); entity_id = int(payload.get("entity_id", 0)); target = str(payload.get("to_status", ""))
    if module not in APPROVABLE: raise HTTPException(400, "Module does not support workflow")
    model = model_for(module); row = db.get(model, entity_id)
    if not row: raise HTTPException(404, "Record not found")
    current = getattr(row, "status", ""); allowed = WORKFLOW.get(module, {}).get(current, [])
    if target not in allowed: raise HTTPException(409, f"Transition {current} -> {target} is not allowed")
    action = "approve" if target in {"approved", "paid", "closed"} else "write"; pid = project_id_for(module, row, db=db); permit(db, user, action, pid, module)
    before = as_dict(row); row.status = target
    if module == "quality" and target == "closed": row.closed_at = datetime.utcnow()
    if module == "changes" and target == "approved": row.approved_date = date.today()
    if module == "document-revisions" and target == "approved": row.approved_by = user.full_name or user.username; row.approval_date = date.today()
    db.add(models_extra.ApprovalAction(project_id=pid, module=module, entity_id=entity_id, from_status=current, to_status=target, action=action, comment=payload.get("comment"), actor_user_id=user.id, actor_name=user.full_name or user.username))
    db.commit(); db.refresh(row); audit(db, user, module, entity_id, "workflow_transition", before, as_dict(row), request)
    return {"record": as_dict(row), "allowed_next": WORKFLOW.get(module, {}).get(target, [])}


@app.get("/api/workflow/{module}/{entity_id}/history")
def history(module: str, entity_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    rows = db.scalars(select(models_extra.ApprovalAction).where(models_extra.ApprovalAction.module == module, models_extra.ApprovalAction.entity_id == entity_id).order_by(models_extra.ApprovalAction.id)).all()
    if rows: permit(db, user, "read", rows[0].project_id, module)
    return [as_dict(r) for r in rows]


def dashboard(db, user, project_id=None):
    today = date.today()
    def count(model, *conds):
        stmt = scoped(select(func.count()).select_from(model), model, user, db, project_id)
        for cond in conds: stmt = stmt.where(cond)
        return int(db.scalar(stmt) or 0)
    total = count(models.Task); done = count(models.Task, models.Task.status.in_(["done", "closed", "completed"])); overdue = count(models.Task, models.Task.due_date < today, ~models.Task.status.in_(["done", "closed", "completed"]))
    quality = count(models.QualityItem, ~models.QualityItem.status.in_(["closed", "approved"])); changes = count(models.ChangeOrder, ~models.ChangeOrder.status.in_(["approved", "rejected", "closed"])); docs = count(models.Document, ~models.Document.status.in_(["approved", "closed"]))
    boq = scoped(select(func.coalesce(func.sum(models.BOQItem.budget_amount), 0), func.coalesce(func.sum(models.BOQItem.actual_amount), 0)), models.BOQItem, user, db, project_id); budget, actual = db.execute(boq).one()
    contracts = db.scalar(scoped(select(func.coalesce(func.sum(models.Contract.contract_value), 0)), models.Contract, user, db, project_id)) or 0
    return {"projects": count(models.Project), "tasks": {"total": total, "done": done, "overdue": overdue, "completion_percent": round(done * 100 / total, 1) if total else 0}, "documents_pending": docs, "quality_open": quality, "changes_pending": changes, "cost": {"budget": float(budget), "actual": float(actual), "variance": float(Decimal(budget) - Decimal(actual))}, "contract_value": float(contracts)}


@app.get("/api/dashboard/summary")
def dashboard_api(project_id: int | None = None, db: Session = Depends(get_db), user=Depends(current_user)):
    if project_id: permit(db, user, "read", project_id, "dashboard")
    return dashboard(db, user, project_id)


@app.get("/api/portfolio/summary")
def portfolio(db: Session = Depends(get_db), user=Depends(current_user)):
    result = []
    for p in db.scalars(scoped(select(models.Project).order_by(models.Project.id.desc()), models.Project, user, db)).all():
        m = dashboard(db, user, p.id); risk = m["tasks"]["overdue"] + m["quality_open"] + m["changes_pending"]
        result.append({**as_dict(p), "health": "red" if risk >= 8 else "amber" if risk >= 3 else "green", "metrics": m})
    return result


@app.get("/api/resources/workload")
def workload(project_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    permit(db, user, "read", project_id, "resources"); out = []
    for r in db.scalars(select(models.Resource).where(models.Resource.project_id == project_id)).all():
        planned = db.scalar(select(func.coalesce(func.sum(models_extra.ResourceAssignment.planned_hours), 0)).where(models_extra.ResourceAssignment.resource_id == r.id)) or 0
        actual = db.scalar(select(func.coalesce(func.sum(models.Timesheet.hours), 0)).where(models.Timesheet.resource_id == r.id)) or 0
        out.append({**as_dict(r), "planned_hours": float(planned), "actual_hours": float(actual)})
    return out


@app.get("/api/search")
def search(q: str = Query(..., min_length=2), project_id: int | None = None, db: Session = Depends(get_db), user=Depends(current_user)):
    out = []
    for module in ["projects", "tasks", "documents", "quality", "changes", "contracts", "procurement"]:
        model = model_for(module); cols = [c for c in inspect(model).columns if isinstance(c.type, (String, Text))]
        if not cols: continue
        stmt = scoped(select(model).where(or_(*[c.ilike(f"%{q}%") for c in cols])), model, user, db, project_id).limit(15)
        out.extend({"module": module, "record": as_dict(row)} for row in db.scalars(stmt).all())
    return out[:100]


@app.get("/api/export/{module}.csv")
def export_csv(module: str, project_id: int | None = None, db: Session = Depends(get_db), user=Depends(current_user)):
    model = model_for(module); rows = db.scalars(scoped(select(model).order_by(model.id), model, user, db, project_id)).all(); output = io.StringIO(); columns = [c.name for c in inspect(model).columns]; writer = csv.DictWriter(output, fieldnames=columns); writer.writeheader()
    for row in rows: writer.writerow(as_dict(row))
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{module}.csv"'})


@app.post("/api/automation/run")
def automation(project_id: int | None = None, db: Session = Depends(get_db), user=Depends(current_user)):
    if project_id: permit(db, user, "write", project_id, "automation")
    today = date.today(); created = 0
    stmt = scoped(select(models.Task).where(models.Task.due_date < today, ~models.Task.status.in_(["done", "closed", "completed"])), models.Task, user, db, project_id)
    for task in db.scalars(stmt).all():
        title = f"Task quá hạn #{task.id}"; exists = db.scalar(select(models.Notification).where(models.Notification.project_id == task.project_id, models.Notification.title == title, models.Notification.is_read.is_(False)))
        if not exists: db.add(models.Notification(project_id=task.project_id, title=title, message=task.title)); created += 1
    stmt = scoped(select(models.Contract).where(models.Contract.end_date.is_not(None), models.Contract.end_date <= today + timedelta(days=30), models.Contract.status == "active"), models.Contract, user, db, project_id)
    for contract in db.scalars(stmt).all():
        title = f"Hợp đồng sắp hết hạn #{contract.id}"; exists = db.scalar(select(models.Notification).where(models.Notification.project_id == contract.project_id, models.Notification.title == title, models.Notification.is_read.is_(False)))
        if not exists: db.add(models.Notification(project_id=contract.project_id, title=title, message=f"{contract.contract_no} - {contract.contractor} - {contract.end_date}")); created += 1
    db.commit(); return {"notifications_created": created, "run_at": datetime.utcnow().isoformat()}


@app.get("/api/ai/risk-summary")
def risk(project_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    permit(db, user, "read", project_id, "automation"); p = db.get(models.Project, project_id)
    if not p: raise HTTPException(404, "Project not found")
    m = dashboard(db, user, project_id); risks = []; score = 0
    if m["tasks"]["overdue"]: risks.append({"type": "schedule", "message": f"{m['tasks']['overdue']} công việc quá hạn"}); score += min(m["tasks"]["overdue"] * 6, 30)
    if m["quality_open"]: risks.append({"type": "quality", "message": f"{m['quality_open']} hồ sơ chất lượng đang mở"}); score += min(m["quality_open"] * 3, 20)
    if m["changes_pending"]: risks.append({"type": "change", "message": f"{m['changes_pending']} VO/Change chưa chốt"}); score += min(m["changes_pending"] * 4, 20)
    if m["cost"]["actual"] > m["cost"]["budget"] > 0: risks.append({"type": "cost", "message": "Chi phí thực tế vượt ngân sách"}); score += 30
    level = "critical" if score >= 70 else "high" if score >= 45 else "medium" if score >= 20 else "low"
    return {"project": {"id": p.id, "code": p.code, "name": p.name}, "risk_score": min(score, 100), "risk_level": level, "risks": risks, "metrics": m}
