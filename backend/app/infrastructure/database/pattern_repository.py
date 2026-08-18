"""Database queries for patterns and their filter catalogs."""

from sqlalchemy import Select, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.database.models import CategoryModel, PatternModel, TagModel


class PatternRepository:
    """Read-only repository for the pattern catalog."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_patterns(
        self,
        search: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[PatternModel]:
        """Return newest patterns matching every supplied filter."""
        statement: Select[tuple[PatternModel]] = select(PatternModel).options(
            selectinload(PatternModel.category),
            selectinload(PatternModel.tags),
        )

        normalized_search = search.strip() if search else ""
        if normalized_search:
            statement = statement.where(
                or_(
                    PatternModel.name.icontains(normalized_search, autoescape=True),
                    PatternModel.tags.any(
                        TagModel.name.icontains(normalized_search, autoescape=True)
                    ),
                )
            )

        normalized_category = category.strip().casefold() if category else ""
        if normalized_category:
            statement = statement.where(
                PatternModel.category.has(func.lower(CategoryModel.slug) == normalized_category)
            )

        normalized_tags = {
            tag.strip().casefold() for tag in (tags or []) if tag.strip()
        }
        for tag in sorted(normalized_tags):
            statement = statement.where(
                PatternModel.tags.any(TagModel.normalized_name == tag)
            )

        statement = statement.order_by(
            PatternModel.created_at.desc(),
            PatternModel.name.asc(),
            PatternModel.id.asc(),
        )
        return list(self._session.scalars(statement).all())

    def list_categories(self) -> list[CategoryModel]:
        """Return categories ordered by display name."""
        return list(self._session.scalars(select(CategoryModel).order_by(CategoryModel.name)).all())

    def list_tags(self) -> list[TagModel]:
        """Return tags ordered case-insensitively by name."""
        return list(self._session.scalars(select(TagModel).order_by(func.lower(TagModel.name))).all())

    def create_pattern(
        self,
        *,
        name: str,
        category_slug: str,
        tag_names: list[str],
        width: int,
        height: int,
        cells: list[list[int | None]],
    ) -> PatternModel:
        """Create a pattern and atomically reuse or create its tags."""
        category = self._session.scalar(
            select(CategoryModel).where(
                func.lower(CategoryModel.slug) == category_slug.casefold()
            )
        )
        if category is None:
            raise ValueError("Unknown pattern category")

        tags: list[TagModel] = []
        for tag_name in tag_names:
            normalized = tag_name.casefold()
            self._session.execute(
                insert(TagModel)
                .values(name=tag_name, normalized_name=normalized)
                .on_conflict_do_nothing(index_elements=[TagModel.normalized_name])
            )
            tag = self._session.scalar(
                select(TagModel).where(TagModel.normalized_name == normalized)
            )
            if tag is None:
                raise RuntimeError("Could not create pattern tag")
            tags.append(tag)

        pattern = PatternModel(
            name=name,
            category=category,
            tags=tags,
            width=width,
            height=height,
            cells=cells,
        )
        self._session.add(pattern)
        self._session.commit()
        self._session.refresh(pattern)
        return pattern

    def rollback(self) -> None:
        """Rollback the current transaction after a failed create operation."""
        self._session.rollback()
