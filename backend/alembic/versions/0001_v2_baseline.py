"""V2 production-beta baseline.

Revision ID: 0001_v2_baseline
Revises:
Create Date: 2026-09-27
"""

from alembic import op

from app.database import Base
from app import models, models_extra  # noqa: F401

revision = "0001_v2_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
