"""Ferramenta de consulta de um deputado."""

from apps.mcp_server.repositories import DeputyRepository


def get_deputy_by_id(repository: DeputyRepository, deputy_id: int) -> dict:
    if deputy_id < 1:
        raise ValueError("deputy_id deve ser positivo")
    deputy = repository.get_by_external_id(deputy_id)
    return deputy or {"message": f"Deputado com id {deputy_id} não encontrado."}
