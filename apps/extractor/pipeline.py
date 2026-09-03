"""Orquestração da ingestão e persistência idempotente."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from packages.shared.database import session_scope
from packages.shared.models import Deputy, IngestionRun, IngestionRunStatus
from sqlalchemy import select, update
from sqlalchemy.engine import Engine

from apps.extractor.client import CâmaraClient
from apps.extractor.schemas import ApiDeputy
from apps.extractor.transform import NormalizedDeputy, normalize_deputy

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IngestionSummary:
    received: int
    inserted: int
    updated: int
    rejected: int


def _changed(existing: Deputy, item: NormalizedDeputy) -> bool:
    return any(
        getattr(existing, field) != value
        for field, value in {
            "name": item.name,
            "party": item.party,
            "state": item.state,
            "email": item.email,
            "photo_url": item.photo_url,
            "source_url": item.source_url,
            "is_active": True,
        }.items()
    )


def _upsert(session, items: list[NormalizedDeputy], ingested_at: datetime) -> tuple[int, int]:
    inserted = updated = 0
    external_ids = [item.external_id for item in items]
    existing_rows = {
        row.external_id: row
        for row in session.scalars(select(Deputy).where(Deputy.external_id.in_(external_ids))).all()
    }
    for item in items:
        row = existing_rows.get(item.external_id)
        if row is None:
            session.add(
                Deputy(
                    external_id=item.external_id,
                    name=item.name,
                    party=item.party,
                    state=item.state,
                    email=item.email,
                    photo_url=item.photo_url,
                    source_url=item.source_url,
                    ingested_at=ingested_at,
                    is_active=True,
                )
            )
            inserted += 1
        else:
            if _changed(row, item):
                row.name = item.name
                row.party = item.party
                row.state = item.state
                row.email = item.email
                row.photo_url = item.photo_url
                row.source_url = item.source_url
                row.updated_at = ingested_at
                updated += 1
            row.ingested_at = ingested_at
            row.is_active = True
    if external_ids:
        session.execute(
            update(Deputy)
            .where(Deputy.is_active.is_(True), Deputy.external_id.not_in(external_ids))
            .values(is_active=False, updated_at=ingested_at)
        )
    return inserted, updated


def run_ingestion(engine: Engine, settings) -> IngestionSummary:
    started_at = datetime.now(UTC)
    source = settings.source_base_url
    with session_scope(engine) as session:
        run = IngestionRun(source=source, started_at=started_at, status=IngestionRunStatus.RUNNING)
        session.add(run)
        session.flush()
        run_id = run.id

    received = rejected = 0
    valid_items: list[NormalizedDeputy] = []
    try:
        with CâmaraClient(settings) as client:
            for raw in client.iter_records():
                received += 1
                try:
                    valid_items.append(normalize_deputy(ApiDeputy.model_validate(raw)))
                except ValueError as exc:
                    rejected += 1
                    logger.warning("registro rejeitado: index=%s motivo=%s", received, exc)
        ingested_at = datetime.now(UTC)
        with session_scope(engine) as session:
            inserted, updated = _upsert(session, valid_items, ingested_at)
        with session_scope(engine) as session:
            run = session.get(IngestionRun, run_id)
            if run is None:
                raise RuntimeError("execução de ingestão não encontrada")
            run.finished_at = ingested_at
            run.status = IngestionRunStatus.SUCCEEDED
            run.records_received = received
            run.records_inserted = inserted
            run.records_updated = updated
            run.records_rejected = rejected
        return IngestionSummary(received, inserted, updated, rejected)
    except Exception as exc:
        logger.exception("ingestão falhou")
        with session_scope(engine) as session:
            run = session.get(IngestionRun, run_id)
            if run is not None:
                run.finished_at = datetime.now(UTC)
                run.status = IngestionRunStatus.FAILED
                run.records_received = received
                run.records_rejected = rejected
                run.error_message = str(exc)[:1000]
        raise
