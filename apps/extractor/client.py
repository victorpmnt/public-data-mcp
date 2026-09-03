"""Cliente HTTP resiliente para a API oficial da Câmara."""

import logging
import time
from collections.abc import Iterator
from typing import Any
from urllib.parse import urljoin

import httpx
from packages.shared.config import Settings

from apps.extractor.schemas import ApiPage

logger = logging.getLogger(__name__)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class CâmaraApiError(RuntimeError):
    """Erro sanitizado ao consultar a API externa."""


class CâmaraClient:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(
                read=settings.http_read_timeout,
                connect=settings.http_connect_timeout,
                write=settings.http_read_timeout,
                pool=settings.http_connect_timeout,
            ),
            headers={"Accept": "application/json"},
        )
        self._owns_client = client is None

    def __enter__(self) -> "CâmaraClient":
        return self

    def __exit__(self, *_: object) -> None:
        if self._owns_client:
            self._client.close()

    def _get_json(self, url: str) -> dict[str, Any]:
        for attempt in range(self.settings.http_max_retries + 1):
            try:
                response = self._client.get(url)
                if (
                    response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.settings.http_max_retries
                ):
                    delay = min(2**attempt, 8)
                    logger.warning(
                        "falha transitória na API: status=%s tentativa=%s",
                        response.status_code,
                        attempt + 1,
                    )
                    time.sleep(delay)
                    continue
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise CâmaraApiError("resposta da API possui formato inválido")
                return payload
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt >= self.settings.http_max_retries:
                    raise CâmaraApiError("falha de comunicação com a API da Câmara") from exc
                time.sleep(min(2**attempt, 8))
            except httpx.HTTPStatusError as exc:
                raise CâmaraApiError(
                    f"API da Câmara retornou HTTP {exc.response.status_code}"
                ) from exc
            except ValueError as exc:
                raise CâmaraApiError("API da Câmara retornou JSON inválido") from exc
        raise CâmaraApiError("não foi possível consultar a API da Câmara")

    def iter_pages(self) -> Iterator[ApiPage]:
        next_url = urljoin(
            self.settings.source_base_url.rstrip("/") + "/",
            self.settings.source_deputies_path.lstrip("/"),
        )
        page_number = 0
        while next_url:
            page_number += 1
            if page_number > 10_000:
                raise CâmaraApiError("paginação excedeu o limite de segurança")
            page = ApiPage.model_validate(self._get_json(next_url))
            logger.info("página da API recebida: page=%s records=%s", page_number, len(page.dados))
            yield page
            next_link = next((link for link in page.links if link.rel == "next"), None)
            next_url = str(next_link.href) if next_link else ""

    def iter_records(self) -> Iterator[dict[str, Any]]:
        for page in self.iter_pages():
            yield from page.dados
