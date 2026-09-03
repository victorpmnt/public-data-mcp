"""Servidor MCP somente leitura via STDIO."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from mcp.server import MCPServer
from packages.shared.config import get_settings
from packages.shared.database import create_mcp_engine

from apps.mcp_server.repositories import DeputyRepository
from apps.mcp_server.tools.count_by_party import count_deputies_by_party
from apps.mcp_server.tools.count_by_state import count_deputies_by_state
from apps.mcp_server.tools.get_data_freshness import get_data_freshness
from apps.mcp_server.tools.get_deputy import get_deputy_by_id
from apps.mcp_server.tools.search_deputies import search_deputies

logger = logging.getLogger(__name__)


def _safe_call[T](function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    try:
        return function(*args, **kwargs)
    except ValueError:
        raise
    except Exception:
        logger.exception("falha interna em ferramenta MCP")
        raise RuntimeError("não foi possível consultar os dados") from None


def create_server(repository: DeputyRepository) -> MCPServer:
    server = MCPServer(
        name="public-data-mcp",
        description="Consultas somente leitura sobre deputados federais em exercício.",
        instructions=(
            "Use as ferramentas para consultar os dados persistidos da Câmara dos Deputados."
        ),
    )

    @server.tool(
        name="search_deputies", description="Busca deputados ativos por nome, partido e UF."
    )
    def search(
        name: str | None = None,
        party: str | None = None,
        state: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        return _safe_call(search_deputies, repository, name, party, state, limit, offset)

    @server.tool(
        name="get_deputy_by_id", description="Consulta um deputado ativo pelo external_id oficial."
    )
    def get_by_id(deputy_id: int) -> dict:
        return _safe_call(get_deputy_by_id, repository, deputy_id)

    @server.tool(
        name="count_deputies_by_party",
        description="Conta deputados ativos por partido, opcionalmente filtrados por UF.",
    )
    def by_party(state: str | None = None) -> dict:
        return _safe_call(count_deputies_by_party, repository, state)

    @server.tool(
        name="count_deputies_by_state",
        description="Conta deputados ativos por estado, opcionalmente filtrados por partido.",
    )
    def by_state(party: str | None = None) -> dict:
        return _safe_call(count_deputies_by_state, repository, party)

    @server.tool(
        name="get_data_freshness",
        description="Retorna a última ingestão bem-sucedida e a quantidade atual de deputados.",
    )
    def freshness() -> dict:
        return _safe_call(get_data_freshness, repository)

    return server


def main() -> None:
    settings = get_settings()
    repository = DeputyRepository(create_mcp_engine(settings))
    server = create_server(repository)
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
