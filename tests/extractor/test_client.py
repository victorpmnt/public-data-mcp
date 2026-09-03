import httpx
from apps.extractor.client import CâmaraClient
from packages.shared.config import Settings


def make_settings() -> Settings:
    return Settings(
        db_admin_password="admin",
        extractor_db_password="extractor",
        mcp_db_password="readonly",
    )


def test_client_follows_next_links() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.path.endswith("/deputados") and request.url.params.get("page") != "2":
            return httpx.Response(
                200,
                json={
                    "dados": [
                        {
                            "id": 1,
                            "nome": "A",
                            "siglaPartido": "X",
                            "siglaUf": "SP",
                            "uri": "https://example.org/1",
                        }
                    ],
                    "links": [
                        {
                            "rel": "next",
                            "href": "https://dadosabertos.camara.leg.br/api/v2/deputados?page=2",
                        }
                    ],
                },
                request=request,
            )
        return httpx.Response(
            200,
            json={
                "dados": [
                    {
                        "id": 2,
                        "nome": "B",
                        "siglaPartido": "Y",
                        "siglaUf": "RJ",
                        "uri": "https://example.org/2",
                    }
                ],
                "links": [],
            },
            request=request,
        )

    with CâmaraClient(
        make_settings(), httpx.Client(transport=httpx.MockTransport(handler))
    ) as client:
        records = list(client.iter_records())
    assert [record["id"] for record in records] == [1, 2]
    assert len(calls) == 2
