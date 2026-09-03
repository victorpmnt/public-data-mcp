"""Ferramenta de atualização dos dados."""

from apps.mcp_server.repositories import DeputyRepository


def get_data_freshness(repository: DeputyRepository) -> dict:
    return repository.freshness()
