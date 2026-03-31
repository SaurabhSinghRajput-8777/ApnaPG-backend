"""initial_schema_5_core_tables

Revision ID: d676f19c8fc9
Revises:
Create Date: 2026-04-01

Creates the 5 core tables for ApnaPG:
  - users
  - properties
  - property_images
  - connections
  - reviews
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d676f19c8fc9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── ENUM types ──────────────────────────────────────────────
    user_role_enum = postgresql.ENUM(
        "tenant", "owner", "admin", name="user_role_enum", create_type=False
    )
    occupancy_type_enum = postgresql.ENUM(
        "single", "double", "triple", name="occupancy_type_enum", create_type=False
    )
    connection_status_enum = postgresql.ENUM(
        "pending", "accepted", "rejected", "active_tenancy", "ended",
        name="connection_status_enum", create_type=False,
    )

    user_role_enum.create(op.get_bind(), checkfirst=True)
    occupancy_type_enum.create(op.get_bind(), checkfirst=True)
    connection_status_enum.create(op.get_bind(), checkfirst=True)

    # ── Table: users ────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("clerk_id", sa.String(255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("profile_image_url", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_clerk_id", "users", ["clerk_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── Table: properties ───────────────────────────────────────
    op.create_table(
        "properties",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("owner_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("locality", sa.String(255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("monthly_rent", sa.Integer(), nullable=False),
        sa.Column("occupancy_type", occupancy_type_enum, nullable=False),
        sa.Column("is_verified_owner", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("house_rules", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_properties_owner_id", "properties", ["owner_id"])
    op.create_index("ix_properties_locality", "properties", ["locality"])
    op.create_index("ix_properties_rent", "properties", ["monthly_rent"])

    # ── Table: property_images ──────────────────────────────────
    op.create_table(
        "property_images",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "property_id",
            sa.UUID(),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("image_url", sa.String(512), nullable=False),
        sa.Column("is_cover_photo", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_property_images_property_id", "property_images", ["property_id"])

    # ── Table: connections ──────────────────────────────────────
    op.create_table(
        "connections",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("property_id", sa.UUID(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", connection_status_enum, server_default="pending", nullable=False),
        sa.Column("tenancy_start_date", sa.Date(), nullable=True),
        sa.Column("tenancy_end_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_connections_tenant_id", "connections", ["tenant_id"])
    op.create_index("ix_connections_property_id", "connections", ["property_id"])
    op.create_index("ix_connections_status", "connections", ["status"])

    # ── Table: reviews ──────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "connection_id",
            sa.UUID(),
            sa.ForeignKey("connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_check_constraint("ck_reviews_rating_range", "reviews", "rating >= 1 AND rating <= 5")
    op.create_index("ix_reviews_connection_id", "reviews", ["connection_id"])
    op.create_index("ix_reviews_target_user_id", "reviews", ["target_user_id"])


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("connections")
    op.drop_table("property_images")
    op.drop_table("properties")
    op.drop_table("users")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS connection_status_enum")
    op.execute("DROP TYPE IF EXISTS occupancy_type_enum")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
