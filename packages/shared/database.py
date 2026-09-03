"""Criação de engines SQLAlchemy por papel de acesso."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from packages.shared.config import Settings, get_settings


def create_database_engine(database_url: str) -> Engine:
    """Cria um engine com validação de conexão antes de cada uso."""

    return create_engine(database_url, pool_pre_ping=True)


def create_admin_engine(settings: Settings | None = None) -> Engine:
    settings = settings or get_settings()
    return create_database_engine(settings.admin_database_url)


def create_extractor_engine(settings: Settings | None = None) -> Engine:
    settings = settings or get_settings()
    return create_database_engine(settings.extractor_database_url)


def create_mcp_engine(settings: Settings | None = None) -> Engine:
    settings = settings or get_settings()
    return create_database_engine(settings.mcp_database_url)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Abre uma sessão e garante commit ou rollback explícito."""

    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
