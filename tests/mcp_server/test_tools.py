from apps.mcp_server.tools.get_deputy import get_deputy_by_id
from apps.mcp_server.tools.search_deputies import search_deputies


class FakeRepository:
    def search(self, name, party, state, limit, offset):
        return {"total": 0, "limit": limit, "offset": offset, "data": []}

    def get_by_external_id(self, external_id):
        return None


def test_search_enforces_maximum_limit() -> None:
    try:
        search_deputies(FakeRepository(), limit=101)
    except ValueError as exc:
        assert "100" in str(exc)
    else:
        raise AssertionError("limite acima de 100 deveria ser rejeitado")


def test_unknown_deputy_returns_clear_message() -> None:
    result = get_deputy_by_id(FakeRepository(), 999)
    assert "não encontrado" in result["message"]
