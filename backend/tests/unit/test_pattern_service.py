"""Unit tests for pattern catalog response mapping."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from app.domain.services.pattern_service import get_categories, get_patterns, get_tags


class FakeRepository:
    """Small repository stub used by the service tests."""

    def list_patterns(self, search=None, category=None, tags=None):
        assert (search, category, tags) == ("rose", "ornament", ["flower"])
        return [
            SimpleNamespace(
                id=UUID("83f9eefc-b6bc-5bdb-b521-c010422068ff"),
                name="Rose",
                category=SimpleNamespace(slug="ornament"),
                tags=[SimpleNamespace(name="flower"), SimpleNamespace(name="роза")],
                width=2,
                height=1,
                cells=[[1, None]],
                created_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
            )
        ]

    def list_categories(self):
        return [SimpleNamespace(slug="alphabet", name="Алфавит")]

    def list_tags(self):
        return [
            SimpleNamespace(
                id=UUID("6f68ca44-0999-578d-a772-078c702cec67"),
                name="flower",
            )
        ]


def test_get_patterns_maps_database_models() -> None:
    """The service should expose the documented public pattern shape."""
    result = get_patterns(FakeRepository(), "rose", "ornament", ["flower"])

    assert result[0].name == "Rose"
    assert result[0].category == "ornament"
    assert result[0].tags == ["flower", "роза"]
    assert result[0].created_at == datetime(2026, 8, 17, tzinfo=timezone.utc)


def test_get_filter_catalogs_map_database_models() -> None:
    """Category and tag services should keep internal UUID policy intact."""
    categories = get_categories(FakeRepository())
    tags = get_tags(FakeRepository())

    assert categories[0].model_dump() == {"slug": "alphabet", "name": "Алфавит"}
    assert tags[0].name == "flower"
