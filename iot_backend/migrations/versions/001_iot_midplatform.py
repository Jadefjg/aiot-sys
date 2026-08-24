"""物联中台核心表：产品/告警/分组/场景 + 设备扩展字段

Revision ID: 001_iot_midplatform
Revises:
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa

revision = "001_iot_midplatform"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("protocol", sa.String(50), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("image_url", sa.String(255), nullable=True),
        sa.Column("is_gateway", sa.Boolean(), server_default="0"),
        sa.Column("smart", sa.Boolean(), server_default="0"),
        sa.Column("controllable", sa.Boolean(), server_default="1"),
        sa.Column("writable", sa.Boolean(), server_default="1"),
        sa.Column("programmable", sa.Boolean(), server_default="0"),
        sa.Column("configurable", sa.Boolean(), server_default="0"),
        sa.Column("ota", sa.Boolean(), server_default="0"),
        sa.Column("locatable", sa.Boolean(), server_default="0"),
        sa.Column("model", sa.JSON(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_products_product_id", "products", ["product_id"])

    op.create_table(
        "device_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("device_groups.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "alarms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("product_id", sa.String(100), nullable=True),
        sa.Column("validator_name", sa.String(100), nullable=True),
        sa.Column("level", sa.String(20), server_default="warning"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("values", sa.JSON(), nullable=True),
        sa.Column("acknowledged", sa.Boolean(), server_default="0"),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_alarms_device_id", "alarms", ["device_id"])
    op.create_index("ix_alarms_created_at", "alarms", ["created_at"])

    op.create_table(
        "scenes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gateway_id", sa.String(100), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="1"),
        sa.Column("time_range", sa.JSON(), nullable=True),
        sa.Column("weekdays", sa.JSON(), nullable=True),
        sa.Column("triggers", sa.JSON(), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("actions", sa.JSON(), nullable=True),
        sa.Column("delay_seconds", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gateway_id", sa.String(100), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="1"),
        sa.Column("cron_time", sa.String(50), nullable=True),
        sa.Column("weekdays", sa.JSON(), nullable=True),
        sa.Column("action", sa.JSON(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("once", sa.Boolean(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "bindings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("gateway_id", sa.String(100), nullable=True),
        sa.Column("device1_id", sa.String(100), nullable=False),
        sa.Column("device2_id", sa.String(100), nullable=False),
        sa.Column("bidirectional", sa.Boolean(), server_default="1"),
        sa.Column("enabled", sa.Boolean(), server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "scripts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gateway_id", sa.String(100), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), server_default="0"),
        sa.Column("delay_seconds", sa.Integer(), server_default="0"),
        sa.Column("repeat_count", sa.Integer(), server_default="0"),
        sa.Column("enabled", sa.Boolean(), server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # 设备表扩展字段（已有表时 ALTER）
    with op.batch_alter_table("devices") as batch:
        batch.add_column(sa.Column("group_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("gateway_id", sa.String(100), nullable=True))
        batch.add_column(sa.Column("link_id", sa.String(100), nullable=True))
        batch.add_column(sa.Column("disabled", sa.Boolean(), server_default="0"))
        batch.add_column(sa.Column("error", sa.Boolean(), server_default="0"))
        batch.add_column(sa.Column("error_string", sa.Text(), nullable=True))
        batch.add_column(sa.Column("geo_code", sa.String(50), nullable=True))
        batch.add_column(sa.Column("values", sa.JSON(), nullable=True))
        batch.create_foreign_key(
            "fk_devices_group_id", "device_groups", ["group_id"], ["id"]
        )
        batch.create_index("ix_devices_gateway_id", ["gateway_id"])
        batch.create_index("ix_devices_product_id", ["product_id"])


def downgrade() -> None:
    with op.batch_alter_table("devices") as batch:
        batch.drop_constraint("fk_devices_group_id", type_="foreignkey")
        batch.drop_index("ix_devices_gateway_id")
        batch.drop_index("ix_devices_product_id")
        for col in (
            "group_id", "gateway_id", "link_id", "disabled",
            "error", "error_string", "geo_code", "values",
        ):
            batch.drop_column(col)
    for table in ("scripts", "bindings", "jobs", "scenes", "alarms", "device_groups", "products"):
        op.drop_table(table)
