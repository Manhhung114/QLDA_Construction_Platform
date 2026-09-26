import json
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, func, inspect, select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from . import models
from .security import create_access_token, decode_access_token, hash_password, verify_password

APP_NAME = "QLDA Construction Platform API"
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=APP_NAME, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
security = HTTPBearer(auto_error=False)

MODULE_REGISTRY = {
    "projects": models.Project,
    "wbs": models.WBSItem,
    "tasks": models.Task,
    "schedule": models.ScheduleActivity,
    "resources": models.Resource,
    "timesheets": models.Timesheet,
    "boq": models.BOQItem,
    "costs": models.CostEntry,
    "contracts": models.Contract,
    "procurement": models.ProcurementOrder,
    "documents": models.Document,
    "document-revisions": models.DocumentRevision,
    "quality": models.QualityItem,
    "changes": models.ChangeOrder,
    "comments": models.Comment,
    "notifications": models.Notification,
    "workflow-rules": models.WorkflowRule,
    "audit-logs": models.AuditLog,
}

MODULE_LABELS = {
    "projects": "Project & Portfolio",
    "tasks": "Task & WBS",
    "schedule": "Schedule",
    "resources": "Resource & Time",
    "boq": "BOQ & Cost Control",
    "contracts": "Contract & Procurement",
    "documents": "Document Control",
    "quality": "Quality / RFI / NCR / INS",
    "changes": "Change Management",
    "comments": "Collaboration",
    "dashboard": "Dashboard & BI",
    "automation": "Automation & AI",
}


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
        existing = db.scalar(select(models.User).where(models.User.username == admin_username))
        if not existing:
            db.add(
                models.User(
                    username=admin_username,
                    email=os.getenv("ADMIN_EMAIL") or None,
                    full_name="System Administrator",
                    role="admin",
                    password_hash=hash_password(admin_password),
                )
            )
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def startup_event() -> None:
    init_database()


def model_to_dict(obj: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in inspect(obj.__class__).columns:
        value = getattr(obj, column.key)
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (date, datetime)):
            value = value.isoformat()
        result[column.key] = value
    return result


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(models.User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive or not found")
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")
    return user


def get_model(module: str):
    model = MODULE_REGISTRY.get(module)
    if not model:
        raise HTTPException(status_code=404, detail=f"Unknown module: {module}")
    return model


def writable_columns(model) -> dict[str, Any]:
    return {
        c.name: c
        for c in inspect(model).columns
        if c.name not in {"id", "created_at", "updated_at"}
    }


def coerce(column, value):
    if value in ("", None):
        return None if column.nullable else value
    if isinstance(column.type, DateTime):
        return datetime.fromisoformat(value) if isinstance(value, str) else value
    if isinstance(column.type, Date):
        return date.fromisoformat(value) if isinstance(value, str) else value
    if isinstance(column.type, Integer):
        return int(value)
    if isinstance(column.type, Numeric):
        return Decimal(str(value))
    if isinstance(column.type, Boolean):
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)
    return value


def clean_payload(model, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = writable_columns(model)
    result = {}
    for key, value in payload.items():
        if key in allowed:
            result[key] = coerce(allowed[key], value)
    return result


def add_audit(
    db: Session,
    user: models.User | None,
    entity_type: str,
    entity_id: int,
    action: str,
    before: dict | None,
    after: dict | None,
) -> None:
    db.add(
        models.AuditLog(
            user_id=user.id if user else None,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_json=json.dumps(before, ensure_ascii=False, default=str) if before else None,
            after_json=json.dumps(after, ensure_ascii=False, default=str) if after else None,
        )
    )
    db.commit()


def project_filter(model, project_id: int | None):
    if project_id is None:
        return None
    if "project_id" in writable_columns(model) or hasattr(model, "project_id"):
        return model.project_id == project_id
    return None


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "version": "1.0.0"}


@app.post("/api/auth/login")
def login(payload: dict[str, Any], db: Session = Depends(get_db)):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    user = db.scalar(select(models.User).where(models.User.username == username))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")
    return {
        "access_token": create_access_token(user.id, user.username, user.role),
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role},
    }


@app.get("/api/auth/me")
def me(user: models.User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "email": user.email, "full_name": user.full_name, "role": user.role}


@app.post("/api/auth/users")
def create_user(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    if not username or len(password) < 8:
        raise HTTPException(status_code=400, detail="Username is required and password must have at least 8 characters")
    if db.scalar(select(models.User).where(models.User.username == username)):
        raise HTTPException(status_code=409, detail="Username already exists")
    user = models.User(
        username=username,
        email=payload.get("email") or None,
        full_name=payload.get("full_name") or username,
        role=payload.get("role") or "member",
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}


@app.get("/api/modules")
def modules_list(_: models.User = Depends(get_current_user)):
    return [{"slug": slug, "label": label} for slug, label in MODULE_LABELS.items()]


@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
):
    original = Path(file.filename or "upload.bin").name
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    target = UPLOAD_DIR / f"{stamp}_{original}"
    content = await file.read()
    max_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {max_mb} MB")
    target.write_bytes(content)
    return {"filename": original, "stored_by": user.username, "url": f"/uploads/{target.name}"}


@app.get("/api/data/{module}")
def list_records(
    module: str,
    project_id: int | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    model = get_model(module)
    stmt = select(model).order_by(model.id.desc()).limit(limit).offset(offset)
    condition = project_filter(model, project_id)
    if condition is not None:
        stmt = stmt.where(condition)
    rows = db.scalars(stmt).all()
    return [model_to_dict(row) for row in rows]


@app.get("/api/data/{module}/{record_id}")
def get_record(
    module: str,
    record_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    model = get_model(module)
    row = db.get(model, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    return model_to_dict(row)


@app.post("/api/data/{module}")
def create_record(
    module: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if module == "audit-logs":
        raise HTTPException(status_code=403, detail="Audit logs are immutable")
    model = get_model(module)
    data = clean_payload(model, payload)
    if module == "contracts" and data.get("start_date") and data.get("duration_days") and not data.get("end_date"):
        data["end_date"] = data["start_date"] + timedelta(days=int(data["duration_days"]))
    row = model(**data)
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot create record: {exc.__class__.__name__}") from exc
    after = model_to_dict(row)
    add_audit(db, user, module, row.id, "create", None, after)
    return after


@app.patch("/api/data/{module}/{record_id}")
def update_record(
    module: str,
    record_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if module == "audit-logs":
        raise HTTPException(status_code=403, detail="Audit logs are immutable")
    model = get_model(module)
    row = db.get(model, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    before = model_to_dict(row)
    data = clean_payload(model, payload)
    for key, value in data.items():
        setattr(row, key, value)
    if module == "contracts" and row.start_date and row.duration_days and "end_date" not in data:
        row.end_date = row.start_date + timedelta(days=int(row.duration_days))
    try:
        db.commit()
        db.refresh(row)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot update record: {exc.__class__.__name__}") from exc
    after = model_to_dict(row)
    add_audit(db, user, module, row.id, "update", before, after)
    return after


@app.delete("/api/data/{module}/{record_id}")
def delete_record(
    module: str,
    record_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if module == "audit-logs":
        raise HTTPException(status_code=403, detail="Audit logs are immutable")
    model = get_model(module)
    row = db.get(model, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    before = model_to_dict(row)
    db.delete(row)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Record is referenced by other data and cannot be deleted") from exc
    add_audit(db, user, module, record_id, "delete", before, None)
    return {"deleted": True, "id": record_id}


def dashboard_payload(db: Session, project_id: int | None = None) -> dict[str, Any]:
    today = date.today()

    def count(model, *conditions):
        stmt = select(func.count()).select_from(model)
        if project_id is not None and hasattr(model, "project_id"):
            stmt = stmt.where(model.project_id == project_id)
        for condition in conditions:
            stmt = stmt.where(condition)
        return int(db.scalar(stmt) or 0)

    task_total = count(models.Task)
    task_done = count(models.Task, models.Task.status.in_(["done", "closed", "completed"]))
    task_overdue = count(
        models.Task,
        models.Task.due_date < today,
        ~models.Task.status.in_(["done", "closed", "completed"]),
    )
    quality_open = count(models.QualityItem, ~models.QualityItem.status.in_(["closed", "approved"]))
    changes_pending = count(models.ChangeOrder, ~models.ChangeOrder.status.in_(["approved", "rejected", "closed"]))
    documents_pending = count(models.Document, ~models.Document.status.in_(["approved", "closed"]))

    boq_stmt = select(func.coalesce(func.sum(models.BOQItem.budget_amount), 0), func.coalesce(func.sum(models.BOQItem.actual_amount), 0))
    if project_id is not None:
        boq_stmt = boq_stmt.where(models.BOQItem.project_id == project_id)
    budget, actual = db.execute(boq_stmt).one()

    contract_stmt = select(func.coalesce(func.sum(models.Contract.contract_value), 0))
    if project_id is not None:
        contract_stmt = contract_stmt.where(models.Contract.project_id == project_id)
    contract_value = db.scalar(contract_stmt) or 0

    return {
        "projects": 1 if project_id is not None else count(models.Project),
        "tasks": {"total": task_total, "done": task_done, "overdue": task_overdue},
        "quality_open": quality_open,
        "changes_pending": changes_pending,
        "documents_pending": documents_pending,
        "cost": {"budget": float(budget), "actual": float(actual), "variance": float(Decimal(budget) - Decimal(actual))},
        "contract_value": float(contract_value),
    }


@app.get("/api/dashboard/summary")
def dashboard_summary(
    project_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    return dashboard_payload(db, project_id)


@app.get("/api/portfolio/summary")
def portfolio_summary(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    projects = db.scalars(select(models.Project).order_by(models.Project.id.desc())).all()
    result = []
    for project in projects:
        item = model_to_dict(project)
        item["health"] = dashboard_payload(db, project.id)
        result.append(item)
    return result


@app.post("/api/workflow/transition")
def workflow_transition(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    module = str(payload.get("module", ""))
    record_id = int(payload.get("id", 0))
    to_status = str(payload.get("to_status", "")).strip()
    model = get_model(module)
    if not hasattr(model, "status"):
        raise HTTPException(status_code=400, detail="This module has no status workflow")
    row = db.get(model, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
    if not to_status:
        raise HTTPException(status_code=400, detail="to_status is required")
    before = model_to_dict(row)
    from_status = row.status
    project_id = getattr(row, "project_id", None)
    rule_stmt = select(models.WorkflowRule).where(
        models.WorkflowRule.module == module,
        models.WorkflowRule.trigger_status == from_status,
        models.WorkflowRule.action_status == to_status,
        models.WorkflowRule.enabled.is_(True),
    )
    if project_id is not None:
        rule_stmt = rule_stmt.where((models.WorkflowRule.project_id == project_id) | (models.WorkflowRule.project_id.is_(None)))
    rule = db.scalar(rule_stmt.limit(1))
    row.status = to_status
    db.commit()
    db.refresh(row)
    after = model_to_dict(row)
    add_audit(db, user, module, row.id, f"status:{from_status}->{to_status}", before, after)
    return {"record": after, "rule_matched": bool(rule), "assigned_to": rule.assign_to if rule else None}


@app.post("/api/automation/run")
def run_automation(
    project_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    today = date.today()
    created = []

    task_stmt = select(models.Task).where(
        models.Task.due_date < today,
        ~models.Task.status.in_(["done", "closed", "completed"]),
    )
    quality_stmt = select(models.QualityItem).where(
        models.QualityItem.due_date < today,
        ~models.QualityItem.status.in_(["closed", "approved"]),
    )
    contract_stmt = select(models.Contract).where(
        models.Contract.end_date >= today,
        models.Contract.end_date <= today + timedelta(days=30),
        ~models.Contract.status.in_(["closed", "cancelled"]),
    )
    if project_id is not None:
        task_stmt = task_stmt.where(models.Task.project_id == project_id)
        quality_stmt = quality_stmt.where(models.QualityItem.project_id == project_id)
        contract_stmt = contract_stmt.where(models.Contract.project_id == project_id)

    alerts: list[tuple[int | None, str, str]] = []
    for task in db.scalars(task_stmt).all():
        alerts.append((task.project_id, f"Task quá hạn #{task.id}", task.title))
    for item in db.scalars(quality_stmt).all():
        alerts.append((item.project_id, f"{item.item_type} quá hạn {item.number}", item.title))
    for contract in db.scalars(contract_stmt).all():
        alerts.append((contract.project_id, f"Hợp đồng sắp hết hạn {contract.contract_no}", contract.contractor))

    for p_id, title, message in alerts:
        exists = db.scalar(
            select(models.Notification).where(
                models.Notification.project_id == p_id,
                models.Notification.title == title,
                models.Notification.is_read.is_(False),
            )
        )
        if not exists:
            note = models.Notification(user_id=user.id, project_id=p_id, title=title, message=message)
            db.add(note)
            created.append(title)
    db.commit()
    return {"alerts_detected": len(alerts), "notifications_created": len(created), "created": created}


@app.get("/api/ai/risk-summary")
def ai_risk_summary(
    project_id: int = Query(...),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    summary = dashboard_payload(db, project_id)
    overdue = summary["tasks"]["overdue"]
    quality_open = summary["quality_open"]
    changes_pending = summary["changes_pending"]
    budget = summary["cost"]["budget"]
    actual = summary["cost"]["actual"]
    overrun_ratio = max(0.0, (actual - budget) / budget) if budget else 0.0

    score = min(100, overdue * 8 + quality_open * 5 + changes_pending * 5 + min(20, int(overrun_ratio * 100)))
    findings = []
    if overdue:
        findings.append(f"Có {overdue} công việc quá hạn cần xử lý.")
    if quality_open:
        findings.append(f"Có {quality_open} hồ sơ/chất lượng đang mở.")
    if changes_pending:
        findings.append(f"Có {changes_pending} VO/Change đang chờ xử lý.")
    if actual > budget and budget:
        findings.append(f"Chi phí thực tế vượt ngân sách {((actual-budget)/budget)*100:.1f}%.")
    if not findings:
        findings.append("Chưa phát hiện tín hiệu rủi ro đáng kể từ dữ liệu hiện tại.")

    level = "low" if score < 30 else "medium" if score < 60 else "high"
    return {
        "project_id": project_id,
        "project": project.name,
        "risk_score": score,
        "risk_level": level,
        "findings": findings,
        "note": "Đây là phân tích quy tắc từ dữ liệu dự án; lớp LLM có thể được cắm thêm sau mà không đổi mô hình dữ liệu.",
    }
