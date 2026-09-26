from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class TimestampMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(40), default="member", index=True)
    can_approve: Mapped[bool] = mapped_column(Boolean, default=False)


class TaskDependency(Base, TimestampMixin):
    __tablename__ = "task_dependencies"
    __table_args__ = (UniqueConstraint("task_id", "predecessor_id", name="uq_task_dependency"),)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    predecessor_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    dependency_type: Mapped[str] = mapped_column(String(8), default="FS")
    lag_days: Mapped[int] = mapped_column(Integer, default=0)


class ChecklistItem(Base, TimestampMixin):
    __tablename__ = "checklist_items"
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(300))
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ResourceAssignment(Base, TimestampMixin):
    __tablename__ = "resource_assignments"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    allocation_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=100)
    planned_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)


class BudgetVersion(Base, TimestampMixin):
    __tablename__ = "budget_versions"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_budget: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class PaymentCertificate(Base, TimestampMixin):
    __tablename__ = "payment_certificates"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), index=True)
    certificate_no: Mapped[str] = mapped_column(String(120))
    period_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    retention_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    status: Mapped[str] = mapped_column(String(50), default="draft")


class Transmittal(Base, TimestampMixin):
    __tablename__ = "transmittals"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    transmittal_no: Mapped[str] = mapped_column(String(120))
    subject: Mapped[str] = mapped_column(String(300))
    sender: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sent_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="sent")


class Claim(Base, TimestampMixin):
    __tablename__ = "claims"
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id"), nullable=True)
    claim_no: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(300))
    claim_type: Mapped[str] = mapped_column(String(60), default="cost")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    extension_days: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class ApprovalAction(Base, TimestampMixin):
    __tablename__ = "approval_actions"
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    module: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
