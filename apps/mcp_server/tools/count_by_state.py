"""Ferramenta de agregação por estado."""

from apps.mcp_server.repositories import DeputyRepository


def count_deputies_by_state(repository: DeputyRepository, party: str | None = None) -> dict:
    return {"data": repository.count_by_state(party)}
