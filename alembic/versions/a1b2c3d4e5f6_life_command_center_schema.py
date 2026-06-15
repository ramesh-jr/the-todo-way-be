"""life command center schema (v3)

Replaces the v2 todo-centric schema with the domains -> priorities -> routines ->
items model, plus standards, reflections, seasons, reviews, calendar connections, and
push subscriptions.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-02 00:00:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
    )


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    """Create the life command center schema."""
    op.create_table(
        "users",
        _uuid_pk(),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("recovery_email", sa.String(320), nullable=True),
        sa.Column("recovery_code_hash", sa.String(255), nullable=True),
        sa.Column(
            "recovery_code_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
        *_timestamps(),
    )

    op.create_table(
        "domains",
        _uuid_pk(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
        sa.Column("icon", sa.String(40), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(20), nullable=False),
        sa.Column("season_note", sa.String(280), nullable=True),
        sa.Column("season_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reflection_only", sa.Boolean(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_domains_user_id", "domains", ["user_id"])

    op.create_table(
        "standards",
        _uuid_pk(),
        sa.Column(
            "domain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domains.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.String(280), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("cadence", sa.String(20), nullable=True),
        sa.Column("target", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_standards_domain_id", "standards", ["domain_id"])

    op.create_table(
        "reflection_entries",
        _uuid_pk(),
        sa.Column(
            "domain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domains.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "standard_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("standards.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_reflection_entries_domain_id", "reflection_entries", ["domain_id"]
    )
    op.create_index(
        "ix_reflection_entries_standard_id", "reflection_entries", ["standard_id"]
    )

    op.create_table(
        "domain_state_logs",
        _uuid_pk(),
        sa.Column(
            "domain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domains.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_state", sa.String(20), nullable=False),
        sa.Column("to_state", sa.String(20), nullable=False),
        sa.Column("note", sa.String(280), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_domain_state_logs_domain_id", "domain_state_logs", ["domain_id"]
    )

    op.create_table(
        "priorities",
        _uuid_pk(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "domain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domains.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(280), nullable=False),
        sa.Column("horizon", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_priorities_user_id", "priorities", ["user_id"])
    op.create_index("ix_priorities_domain_id", "priorities", ["domain_id"])
    op.create_index("ix_priorities_period_start", "priorities", ["period_start"])

    op.create_table(
        "routines",
        _uuid_pk(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "domain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domains.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "standard_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("standards.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(280), nullable=False),
        sa.Column("rrule", sa.String(500), nullable=False),
        sa.Column("default_energy", sa.String(10), nullable=True),
        sa.Column("default_context", sa.JSON(), nullable=False),
        sa.Column("default_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("last_generated_date", sa.Date(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_routines_user_id", "routines", ["user_id"])
    op.create_index("ix_routines_domain_id", "routines", ["domain_id"])
    op.create_index("ix_routines_standard_id", "routines", ["standard_id"])

    op.create_table(
        "labels",
        _uuid_pk(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
    )
    op.create_index("ix_labels_user_id", "labels", ["user_id"])

    op.create_table(
        "items",
        _uuid_pk(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column(
            "domain_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domains.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "priority_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("priorities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "routine_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("routines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "standard_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("standards.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("energy", sa.String(10), nullable=True),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("urgency", sa.String(10), nullable=False),
        sa.Column("rrule", sa.String(500), nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("external_calendar_id", sa.String(255), nullable=True),
        sa.Column("someday_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_items_user_id", "items", ["user_id"])
    op.create_index("ix_items_status", "items", ["status"])
    op.create_index("ix_items_domain_id", "items", ["domain_id"])
    op.create_index("ix_items_priority_id", "items", ["priority_id"])
    op.create_index("ix_items_routine_id", "items", ["routine_id"])
    op.create_index("ix_items_standard_id", "items", ["standard_id"])
    op.create_index("ix_items_scheduled_at", "items", ["scheduled_at"])
    op.create_index("ix_items_external_id", "items", ["external_id"])
    op.create_index("ix_items_user_status", "items", ["user_id", "status"])
    op.create_index("ix_items_user_domain", "items", ["user_id", "domain_id"])
    op.create_index("ix_items_user_scheduled", "items", ["user_id", "scheduled_at"])

    op.create_table(
        "item_labels",
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("item_id", "label_id"),
    )

    op.create_table(
        "reminders",
        _uuid_pk(),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("offset_type", sa.String(20), nullable=False),
    )
    op.create_index("ix_reminders_item_id", "reminders", ["item_id"])

    op.create_table(
        "calendar_connections",
        _uuid_pk(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("account_email", sa.String(320), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_token", sa.Text(), nullable=True),
        sa.Column("calendar_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
    )
    op.create_index(
        "ix_calendar_connections_user_id", "calendar_connections", ["user_id"]
    )

    op.create_table(
        "reviews",
        _uuid_pk(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("deferred_reason", sa.String(280), nullable=True),
        sa.Column("deferred_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])

    op.create_table(
        "push_subscriptions",
        _uuid_pk(),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.Text(), nullable=False, unique=True),
        sa.Column("p256dh", sa.String(255), nullable=False),
        sa.Column("auth", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"]
    )


def downgrade() -> None:
    """Drop the life command center schema."""
    op.drop_table("push_subscriptions")
    op.drop_table("reviews")
    op.drop_table("calendar_connections")
    op.drop_table("reminders")
    op.drop_table("item_labels")
    op.drop_table("items")
    op.drop_table("labels")
    op.drop_table("routines")
    op.drop_table("priorities")
    op.drop_table("domain_state_logs")
    op.drop_table("reflection_entries")
    op.drop_table("standards")
    op.drop_table("domains")
    op.drop_table("users")
