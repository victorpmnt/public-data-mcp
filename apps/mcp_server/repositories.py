"""Consultas parametrizadas usadas pelas ferramentas MCP."""

from packages.shared.models import Deputy, IngestionRun, IngestionRunStatus
from sqlalchemy import func, select
from sqlalchemy.engine import Engine


class DeputyRepository:
    """Repositório de consultas somente leitura."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def search(
        self, name: str | None, party: str | None, state: str | None, limit: int, offset: int
    ) -> dict:
        filters = [Deputy.is_active.is_(True)]
        if name:
            filters.append(Deputy.name.ilike(f"%{name.strip()}%"))
        if party:
            filters.append(Deputy.party == party.strip().upper())
        if state:
            filters.append(Deputy.state == state.strip().upper())
        with self.engine.connect() as connection:
            total = connection.scalar(select(func.count()).select_from(Deputy).where(*filters)) or 0
            rows = (
                connection.execute(
                    select(Deputy)
                    .where(*filters)
                    .order_by(Deputy.name.asc(), Deputy.external_id.asc())
                    .limit(limit)
                    .offset(offset)
                )
                .mappings()
                .all()
            )
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": [
                {
                    "external_id": row["external_id"],
                    "name": row["name"],
                    "party": row["party"],
                    "state": row["state"],
                    "email": row["email"],
                    "photo_url": row["photo_url"],
                }
                for row in rows
            ],
        }

    def get_by_external_id(self, external_id: int) -> dict | None:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    select(Deputy).where(
                        Deputy.external_id == external_id, Deputy.is_active.is_(True)
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return {
            "external_id": row["external_id"],
            "name": row["name"],
            "party": row["party"],
            "state": row["state"],
            "email": row["email"],
            "photo_url": row["photo_url"],
            "source_url": row["source_url"],
        }

    def count_by_party(self, state: str | None) -> list[dict]:
        filters = [Deputy.is_active.is_(True)]
        if state:
            filters.append(Deputy.state == state.strip().upper())
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(Deputy.party.label("key"), func.count().label("count"))
                .where(*filters)
                .group_by(Deputy.party)
                .order_by(func.count().desc(), Deputy.party.asc())
            ).all()
        return [{"party": row.key, "count": row.count} for row in rows]

    def count_by_state(self, party: str | None) -> list[dict]:
        filters = [Deputy.is_active.is_(True)]
        if party:
            filters.append(Deputy.party == party.strip().upper())
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(Deputy.state.label("key"), func.count().label("count"))
                .where(*filters)
                .group_by(Deputy.state)
                .order_by(func.count().desc(), Deputy.state.asc())
            ).all()
        return [{"state": row.key, "count": row.count} for row in rows]

    def freshness(self) -> dict:
        with self.engine.connect() as connection:
            latest = (
                connection.execute(
                    select(IngestionRun)
                    .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
                    .limit(1)
                )
                .mappings()
                .first()
            )
            successful_at = connection.scalar(
                select(func.max(IngestionRun.finished_at)).where(
                    IngestionRun.status == IngestionRunStatus.SUCCEEDED
                )
            )
            deputy_count = (
                connection.scalar(
                    select(func.count()).select_from(Deputy).where(Deputy.is_active.is_(True))
                )
                or 0
            )
        return {
            "last_successful_ingestion_at": successful_at,
            "current_deputy_count": deputy_count,
            "source": latest["source"] if latest else None,
            "last_run_status": latest["status"].value if latest else None,
            "records_processed": latest["records_received"] if latest else 0,
        }
