import asyncio

from apps.mcp_server.server import create_server


def test_server_exposes_only_expected_tools() -> None:
    server = create_server(object())
    tools = asyncio.run(server.list_tools())
    assert {tool.name for tool in tools} == {
        "search_deputies",
        "get_deputy_by_id",
        "count_deputies_by_party",
        "count_deputies_by_state",
        "get_data_freshness",
    }
