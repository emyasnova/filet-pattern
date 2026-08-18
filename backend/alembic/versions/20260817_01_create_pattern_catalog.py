"""Create and seed the pattern catalog.

Revision ID: 20260817_01
Revises: None
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260817_01"
down_revision = None
branch_labels = None
depends_on = None

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "patterns.json"
SEED_NAMESPACE = uuid.UUID("3cf4c068-2a36-4f25-99a4-c04137796860")
SEED_CREATED_AT = datetime(2026, 8, 17, tzinfo=timezone.utc)
CATEGORY_NAMES = {
    "alphabet": "Алфавит",
    "frame": "Рамки",
    "object": "Объекты",
    "ornament": "Орнаменты",
}


def _seed_uuid(kind: str, value: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, f"{kind}:{value}")


def upgrade() -> None:
    categories = op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=128), nullable=False),
    )
    tags = op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("normalized_name", sa.String(length=128), nullable=False, unique=True),
    )
    patterns = op.create_table(
        "patterns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("cells", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("width > 0", name="ck_patterns_width_positive"),
        sa.CheckConstraint("height > 0", name="ck_patterns_height_positive"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
    )
    pattern_tags = op.create_table(
        "pattern_tags",
        sa.Column("pattern_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["pattern_id"], ["patterns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pattern_id", "tag_id"),
    )
    op.create_index("ix_patterns_category_id", "patterns", ["category_id"])
    op.create_index("ix_patterns_created_at", "patterns", [sa.text("created_at DESC")])
    op.create_index("ix_pattern_tags_tag_id", "pattern_tags", ["tag_id"])

    seed_patterns = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    category_rows = [
        {"id": _seed_uuid("category", slug), "slug": slug, "name": name}
        for slug, name in CATEGORY_NAMES.items()
    ]
    op.bulk_insert(categories, category_rows)

    tag_names: dict[str, str] = {}
    for pattern in seed_patterns:
        for tag in pattern["tags"]:
            tag_names.setdefault(tag.casefold(), tag)
    tag_rows = [
        {
            "id": _seed_uuid("tag", normalized),
            "name": name,
            "normalized_name": normalized,
        }
        for normalized, name in sorted(tag_names.items())
    ]
    op.bulk_insert(tags, tag_rows)

    pattern_rows = []
    link_rows = []
    for pattern in seed_patterns:
        pattern_id = _seed_uuid("pattern", pattern["source_id"])
        pattern_rows.append(
            {
                "id": pattern_id,
                "name": pattern["name"],
                "category_id": _seed_uuid("category", pattern["category"]),
                "width": pattern["width"],
                "height": pattern["height"],
                "cells": pattern["cells"],
                "created_at": SEED_CREATED_AT,
            }
        )
        link_rows.extend(
            {
                "pattern_id": pattern_id,
                "tag_id": _seed_uuid("tag", tag.casefold()),
            }
            for tag in pattern["tags"]
        )
    op.bulk_insert(patterns, pattern_rows)
    op.bulk_insert(pattern_tags, link_rows)


def downgrade() -> None:
    op.drop_index("ix_pattern_tags_tag_id", table_name="pattern_tags")
    op.drop_table("pattern_tags")
    op.drop_index("ix_patterns_created_at", table_name="patterns")
    op.drop_index("ix_patterns_category_id", table_name="patterns")
    op.drop_table("patterns")
    op.drop_table("tags")
    op.drop_table("categories")
