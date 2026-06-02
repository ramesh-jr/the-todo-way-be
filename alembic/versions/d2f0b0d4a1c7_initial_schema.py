"""initial schema

Revision ID: d2f0b0d4a1c7
Revises: 
Create Date: 2026-02-10 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d2f0b0d4a1c7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema tables and indexes."""
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("username", sa.String(length=100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "sections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sections_user_id", "sections", ["user_id"])

    op.create_table(
        "subsections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sections.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )
    op.create_index("ix_subsections_section_id", "subsections", ["section_id"])

    op.create_table(
        "labels",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
    )
    op.create_index("ix_labels_user_id", "labels", ["user_id"])

    op.create_table(
        "todos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scheduled_date", sa.DateTime(), nullable=True),
        sa.Column("deadline_date", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("priority", sa.String(length=2), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sections.id"),
            nullable=True,
        ),
        sa.Column(
            "subsection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subsections.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_todos_user_id", "todos", ["user_id"])
    op.create_index("ix_todos_scheduled_date", "todos", ["scheduled_date"])
    op.create_index("ix_todos_deadline_date", "todos", ["deadline_date"])
    op.create_index("ix_todos_is_completed", "todos", ["is_completed"])
    op.create_index("ix_todos_section_id", "todos", ["section_id"])
    op.create_index(
        "ix_todos_user_completed", "todos", ["user_id", "is_completed"]
    )
    op.create_index("ix_todos_user_section", "todos", ["user_id", "section_id"])
    op.create_index(
        "ix_todos_user_scheduled", "todos", ["user_id", "scheduled_date"]
    )

    op.create_table(
        "todo_labels",
        sa.Column(
            "todo_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "label_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["todo_id"],
            ["todos.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["label_id"],
            ["labels.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("todo_id", "label_id"),
    )

    op.create_table(
        "reminders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "todo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("todos.id"),
            nullable=False,
        ),
        sa.Column("remind_at", sa.DateTime(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
    )
    op.create_index("ix_reminders_todo_id", "reminders", ["todo_id"])


def downgrade() -> None:
    """Drop initial schema tables and indexes."""
    op.drop_index("ix_reminders_todo_id", table_name="reminders")
    op.drop_table("reminders")

    op.drop_table("todo_labels")

    op.drop_index("ix_todos_user_scheduled", table_name="todos")
    op.drop_index("ix_todos_user_section", table_name="todos")
    op.drop_index("ix_todos_user_completed", table_name="todos")
    op.drop_index("ix_todos_section_id", table_name="todos")
    op.drop_index("ix_todos_is_completed", table_name="todos")
    op.drop_index("ix_todos_deadline_date", table_name="todos")
    op.drop_index("ix_todos_scheduled_date", table_name="todos")
    op.drop_index("ix_todos_user_id", table_name="todos")
    op.drop_table("todos")

    op.drop_index("ix_labels_user_id", table_name="labels")
    op.drop_table("labels")

    op.drop_index("ix_subsections_section_id", table_name="subsections")
    op.drop_table("subsections")

    op.drop_index("ix_sections_user_id", table_name="sections")
    op.drop_table("sections")

    op.drop_table("users")
