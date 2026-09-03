"""Configuração carregada exclusivamente de variáveis de ambiente."""

from functools import lru_cache
from typing import Annotated
from urllib.parse import quote

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração do projeto para os três papéis de banco e a API externa."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_host: str = "localhost"
    db_port: Annotated[int, Field(ge=1, le=65535)] = 5432
    db_name: str = "public_data"
    db_admin_user: str = "postgres_admin"
    db_admin_password: str
    extractor_db_user: str = "extractor_user"
    extractor_db_password: str
    mcp_db_user: str = "mcp_readonly"
    mcp_db_password: str

    source_base_url: str = "https://dadosabertos.camara.leg.br/api/v2"
    source_deputies_path: str = "/deputados?ordem=ASC&ordenarPor=nome&itens=100"
    http_connect_timeout: Annotated[float, Field(gt=0)] = 5.0
    http_read_timeout: Annotated[float, Field(gt=0)] = 30.0
    http_max_retries: Annotated[int, Field(ge=0, le=5)] = 3
    mcp_default_limit: Annotated[int, Field(ge=1, le=100)] = 20
    mcp_max_limit: Annotated[int, Field(ge=1, le=100)] = 100

    def database_url(self, user: str, password: str) -> str:
        """Monta uma URL Psycopg com credenciais corretamente escapadas."""

        return (
            f"postgresql+psycopg://{quote(user, safe='')}:{quote(password, safe='')}@"
            f"{self.db_host}:{self.db_port}/{quote(self.db_name, safe='')}"
        )

    @property
    def admin_database_url(self) -> str:
        return self.database_url(self.db_admin_user, self.db_admin_password)

    @property
    def extractor_database_url(self) -> str:
        return self.database_url(self.extractor_db_user, self.extractor_db_password)

    @property
    def mcp_database_url(self) -> str:
        return self.database_url(self.mcp_db_user, self.mcp_db_password)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna uma instância cacheada para evitar leituras inconsistentes do ambiente."""

    return Settings()
