"""为告警增加恢复状态字段"""
from alembic import op
import sqlalchemy as sa

revision = "002_alarm_recovery_fields"
down_revision = "001_iot_midplatform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alarms", sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("alarms", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    op.create_index("ix_alarms_resolved", "alarms", ["resolved"])


def downgrade() -> None:
    op.drop_index("ix_alarms_resolved", table_name="alarms")
    op.drop_column("alarms", "resolved_at")
    op.drop_column("alarms", "resolved")
