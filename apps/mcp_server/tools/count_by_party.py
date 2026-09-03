"""Ferramenta de agregação por partido."""

from apps.mcp_server.repositories import DeputyRepository


def count_deputies_by_party(repository: DeputyRepository, state: str | None = None) -> dict:
    if state is not None and (len(state.strip()) != 2 or not state.strip().isalpha()):
        raise ValueError("state deve ser uma UF de duas letras")
    return {"data": repository.count_by_party(state)}
