from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class TimestampMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(40), default="member")
    password_hash: Mapped[str] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="planning")
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    budget: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    manager: Mapped[str | None] = mapped_column(String(200), nullable=True)


class WBSItem(Base, TimestampMixin):
    __tablename__ = "wbs_items"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(250))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("wbs_items.id"), nullable=True)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=0)
    progress: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    wbs_id: Mapped[int | None] = mapped_column(ForeignKey("wbs_items.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="todo")
    priority: Mapped[str] = mapped_column(String(30), default="medium")
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    baseline_start: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    baseline_due: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    progress: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    predecessor_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)


class ScheduleActivity(Base, TimestampMixin):
    __tablename__ = "schedule_activities"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    activity_code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(300))
    planned_start: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    planned_end: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    progress: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    critical: Mapped[bool] = mapped_column(Boolean, default=False)
    predecessor_ids: Mapped[str | None] = mapped_column(String(500), nullable=True)
    milestone: Mapped[bool] = mapped_column(Boolean, default=False)


class Resource(Base, TimestampMixin):
    __tablename__ = "resources"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    resource_type: Mapped[str] = mapped_column(String(50), default="person")
    capacity_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=8)
    cost_rate: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(40), default="active")


class Timesheet(Base, TimestampMixin):
    __tablename__ = "timesheets"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    work_date: Mapped[datetime] = mapped_column(Date)
    hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class BOQItem(Base, TimestampMixin):
    __tablename__ = "boq_items"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    item_code: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    unit_rate: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    actual_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)


class CostEntry(Base, TimestampMixin):
    __tablename__ = "cost_entries"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    boq_item_id: Mapped[int | None] = mapped_column(ForeignKey("boq_items.id"), nullable=True)
    cost_type: Mapped[str] = mapped_column(String(50), default="actual")
    description: Mapped[str] = mapped_column(String(300))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    entry_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)


class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    contract_no: Mapped[str] = mapped_column(String(120))
    contractor: Mapped[str] = mapped_column(String(250))
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")


class ProcurementOrder(Base, TimestampMixin):
    __tablename__ = "procurement_orders"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    po_no: Mapped[str] = mapped_column(String(120))
    vendor: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    expected_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="requested")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    document_no: Mapped[str] = mapped_column(String(150))
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(80), default="general")
    discipline: Mapped[str | None] = mapped_column(String(80), nullable=True)
    current_revision: Mapped[str] = mapped_column(String(30), default="00")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class DocumentRevision(Base, TimestampMixin):
    __tablename__ = "document_revisions"
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    revision: Mapped[str] = mapped_column(String(30))
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    approval_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="submitted")


class QualityItem(Base, TimestampMixin):
    __tablename__ = "quality_items"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    item_type: Mapped[str] = mapped_column(String(40), default="RFI")
    number: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    raised_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(200), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ChangeOrder(Base, TimestampMixin):
    __tablename__ = "change_orders"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    vo_no: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(300))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_impact: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    time_impact_days: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    submitted_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    approved_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int] = mapped_column(Integer)
    author: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(250))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkflowRule(Base, TimestampMixin):
    __tablename__ = "workflow_rules"
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    module: Mapped[str] = mapped_column(String(80))
    trigger_status: Mapped[str] = mapped_column(String(50))
    action_status: Mapped[str] = mapped_column(String(50))
    assign_to: Mapped[str | None] = mapped_column(String(200), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(50))
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
