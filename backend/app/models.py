from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, Numeric, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default='')
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default='member')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Project(Base, TimestampMixin):
    __tablename__ = 'projects'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default='planning')
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget: Mapped[Decimal] = mapped_column(Numeric(18,2), default=0)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default='')

class WBSItem(Base, TimestampMixin):
    __tablename__ = 'wbs_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey('wbs_items.id'), nullable=True)
    code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(255))

class Task(Base, TimestampMixin):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    wbs_id: Mapped[int | None] = mapped_column(ForeignKey('wbs_items.id'), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default='todo')
    priority: Mapped[str] = mapped_column(String(30), default='medium')
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    predecessor_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)

class ScheduleItem(Base, TimestampMixin):
    __tablename__ = 'schedule_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey('tasks.id'), nullable=True)
    baseline_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    baseline_finish: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_finish: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_milestone: Mapped[bool] = mapped_column(Boolean, default=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)

class Resource(Base, TimestampMixin):
    __tablename__ = 'resources'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    name: Mapped[str] = mapped_column(String(255))
    resource_type: Mapped[str] = mapped_column(String(50), default='labor')
    capacity_hours_week: Mapped[Decimal] = mapped_column(Numeric(10,2), default=40)
    cost_rate: Mapped[Decimal] = mapped_column(Numeric(18,2), default=0)

class BOQItem(Base, TimestampMixin):
    __tablename__ = 'boq_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    code: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(30), default='')
    quantity: Mapped[Decimal] = mapped_column(Numeric(18,3), default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18,2), default=0)
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(18,3), default=0)

class Contract(Base, TimestampMixin):
    __tablename__ = 'contracts'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    contract_no: Mapped[str] = mapped_column(String(120))
    vendor: Mapped[str] = mapped_column(String(255))
    value: Mapped[Decimal] = mapped_column(Numeric(18,2), default=0)
    status: Mapped[str] = mapped_column(String(50), default='draft')
    signed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

class Document(Base, TimestampMixin):
    __tablename__ = 'documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    document_no: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(80), default='general')
    revision: Mapped[str] = mapped_column(String(30), default='00')
    status: Mapped[str] = mapped_column(String(50), default='draft')
    file_path: Mapped[str] = mapped_column(String(500), default='')

class QualityItem(Base, TimestampMixin):
    __tablename__ = 'quality_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    number: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default='draft')
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(Text, default='')

class ChangeRequest(Base, TimestampMixin):
    __tablename__ = 'change_requests'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    number: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    change_type: Mapped[str] = mapped_column(String(50), default='vo')
    amount: Mapped[Decimal] = mapped_column(Numeric(18,2), default=0)
    time_impact_days: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default='draft')

class Comment(Base, TimestampMixin):
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), index=True)
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int] = mapped_column(Integer)
    author_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    body: Mapped[str] = mapped_column(Text)

class WorkflowRule(Base, TimestampMixin):
    __tablename__ = 'workflow_rules'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey('projects.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    entity_type: Mapped[str] = mapped_column(String(80))
    trigger_event: Mapped[str] = mapped_column(String(80))
    condition_json: Mapped[dict] = mapped_column(JSON, default=dict)
    action_json: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    before_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
