"""Label ORM model (optional color tags for items)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.user import User


class Label(Base):
    """Color-coded tag for categorizing items."""

    __tablename__ = "labels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(7))  # hex color e.g. #FF5733

    # Relationships
    user: Mapped[User] = relationship(back_populates="labels")
    items: Mapped[list[Item]] = relationship(
        secondary="item_labels", back_populates="labels"
    )
