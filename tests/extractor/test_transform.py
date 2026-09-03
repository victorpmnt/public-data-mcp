from apps.extractor.schemas import ApiDeputy
from apps.extractor.transform import normalize_deputy


def test_normalize_deputy_cleans_values() -> None:
    record = ApiDeputy.model_validate(
        {
            "id": 1,
            "nome": "  Maria   Silva ",
            "siglaPartido": "  abc ",
            "siglaUf": " sp ",
            "email": "  maria@example.org  ",
            "urlFoto": "https://example.org/photo.jpg",
            "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/1",
        }
    )
    normalized = normalize_deputy(record)
    assert normalized.name == "Maria Silva"
    assert normalized.party == "ABC"
    assert normalized.state == "SP"
    assert normalized.email == "maria@example.org"


def test_invalid_deputy_is_rejected() -> None:
    record = ApiDeputy.model_validate(
        {
            "id": 1,
            "nome": "Deputado",
            "siglaPartido": "PARTIDO",
            "siglaUf": "São Paulo",
            "uri": "https://example.org/deputies/1",
        }
    )
    try:
        normalize_deputy(record)
    except ValueError as exc:
        assert "UF" in str(exc)
    else:
        raise AssertionError("UF inválida deveria ser rejeitada")
