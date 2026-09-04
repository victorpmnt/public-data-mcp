from datetime import UTC, datetime

from apps.extractor.pipeline import _deduplicate, _safe_error_message, _upsert
from apps.extractor.transform import NormalizedDeputy
from packages.shared.models import Base, Deputy
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


def test_upsert_is_idempotent_and_reactivates_rows() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime.now(UTC)
    item = NormalizedDeputy(1, "Ana Silva", "ABC", "SP", None, None, "https://example.org/1")
    with Session(engine) as session:
        assert _upsert(session, [item], now) == (1, 0)
        session.commit()
        assert _upsert(session, [item], now) == (0, 0)
        session.commit()
        row = session.scalar(select(Deputy).where(Deputy.external_id == 1))
        assert row is not None and row.is_active is True


def test_deduplicate_keeps_first_external_id() -> None:
    first = NormalizedDeputy(1, "Primeiro", "ABC", "SP", None, None, "https://example.org/1")
    second = NormalizedDeputy(1, "Segundo", "ABC", "SP", None, None, "https://example.org/1")
    assert _deduplicate([first, second]) == [first]


def test_unexpected_error_message_is_sanitized() -> None:
    error = RuntimeError("password=secret host=internal-db.example")
    assert _safe_error_message(error) == "falha interna durante a ingestão"
