"""Persist Agent Workflow thread identities."""
from alembic import op
import sqlalchemy as sa

revision = "003_agent_workflows"
down_revision = "002_alarm_recovery_fields"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("agent_workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column("owner_id", sa.String(100), nullable=False),
        sa.Column("thread_id", sa.String(255), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("workflow_name", "owner_id", name="uq_agent_workflow_owner"),
        sa.UniqueConstraint("thread_id", name="uq_agent_workflows_thread_id"),
    )
    op.create_index("ix_agent_workflows_workflow_name", "agent_workflows", ["workflow_name"])
    op.create_index("ix_agent_workflows_owner_id", "agent_workflows", ["owner_id"])
    op.create_index("ix_agent_workflows_thread_id", "agent_workflows", ["thread_id"])

def downgrade():
    op.drop_table("agent_workflows")
