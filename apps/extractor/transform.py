"""Normalização pura dos registros recebidos da API."""

from dataclasses import dataclass

from apps.extractor.schemas import ApiDeputy


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


@dataclass(frozen=True, slots=True)
class NormalizedDeputy:
    external_id: int
    name: str
    party: str
    state: str
    email: str | None
    photo_url: str | None
    source_url: str


def normalize_deputy(record: ApiDeputy) -> NormalizedDeputy:
    """Converte um registro validado para o formato persistido."""

    name = _clean(record.name)
    party = _clean(record.party)
    state = _clean(record.state)
    if not name:
        raise ValueError("nome do deputado vazio")
    if not party:
        raise ValueError("partido do deputado vazio")
    if not state or len(state) != 2 or not state.isalpha():
        raise ValueError("UF do deputado inválida")

    return NormalizedDeputy(
        external_id=record.external_id,
        name=name,
        party=party.upper(),
        state=state.upper(),
        email=_clean(record.email),
        photo_url=str(record.photo_url) if record.photo_url else None,
        source_url=str(record.source_url),
    )
