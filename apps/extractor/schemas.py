"""Schemas das respostas da API de Dados Abertos."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ApiLink(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rel: str
    href: HttpUrl


class ApiPage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dados: list[dict[str, Any]] = Field(default_factory=list)
    links: list[ApiLink] = Field(default_factory=list)


class ApiDeputy(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    external_id: int = Field(alias="id", gt=0)
    name: str = Field(alias="nome", min_length=1)
    party: str = Field(default="", alias="siglaPartido")
    state: str = Field(default="", alias="siglaUf")
    email: str | None = None
    photo_url: HttpUrl | None = Field(default=None, alias="urlFoto")
    source_url: HttpUrl = Field(alias="uri")
