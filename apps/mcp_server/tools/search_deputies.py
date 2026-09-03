"""Ferramenta de busca de deputados."""

from apps.mcp_server.repositories import DeputyRepository


def search_deputies(
    repository: DeputyRepository,
    name: str | None = None,
    party: str | None = None,
    state: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    if limit < 1 or limit > 100:
        raise ValueError("limit deve estar entre 1 e 100")
    if offset < 0:
        raise ValueError("offset não pode ser negativo")
    if state is not None and (len(state.strip()) != 2 or not state.strip().isalpha()):
        raise ValueError("state deve ser uma UF de duas letras")
    return repository.search(name, party, state, limit, offset)
