"""SQLAlchemy models for the pattern catalog."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Table, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.infrastructure.database.base import Base

pattern_tags = Table(
    "pattern_tags",
    Base.metadata,
    Column("pattern_id", Uuid(as_uuid=True), ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Uuid(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class CategoryModel(Base):
    """Pattern category persisted in PostgreSQL."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    patterns: Mapped[list[PatternModel]] = relationship(back_populates="category")


class TagModel(Base):
    """Normalized searchable pattern tag."""

    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    patterns: Mapped[list[PatternModel]] = relationship(
        secondary=pattern_tags,
        back_populates="tags",
    )


class PatternModel(Base):
    """Reusable filet pattern stored as a cell matrix."""

    __tablename__ = "patterns"
    __table_args__ = (
        CheckConstraint("width > 0", name="ck_patterns_width_positive"),
        CheckConstraint("height > 0", name="ck_patterns_height_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    width: Mapped[int] = mapped_column(nullable=False)
    height: Mapped[int] = mapped_column(nullable=False)
    cells: Mapped[list[list[int | None]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    category: Mapped[CategoryModel] = relationship(back_populates="patterns")
    tags: Mapped[list[TagModel]] = relationship(
        secondary=pattern_tags,
        back_populates="patterns",
        order_by=TagModel.name,
    )
