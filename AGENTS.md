# AGENTS.md

## Propósito

Este arquivo orienta agentes de desenvolvimento que trabalham neste repositório. O objetivo do projeto é entregar um MVP seguro, testável e bem documentado que ingere dados públicos de deputados federais a partir da API oficial da Câmara dos Deputados, persiste os dados no PostgreSQL e os disponibiliza por meio de ferramentas MCP somente leitura.

Leia também `RULES.md` antes de modificar código. Consulte `SKILLS.md` para identificar os conhecimentos e práticas esperados em cada etapa.

## Objetivo do produto

O sistema deve:

1. Consumir exclusivamente a API de Dados Abertos da Câmara dos Deputados, sem scraping.
2. Percorrer corretamente todas as páginas do endpoint de deputados em exercício.
3. Validar e normalizar as respostas externas.
4. Persistir deputados por `external_id` usando carga idempotente.
5. Registrar cada execução em `ingestion_runs`.
6. Expor consultas controladas por um servidor MCP com transporte STDIO.
7. Garantir que o MCP acesse o PostgreSQL com um usuário somente leitura.

Documentação oficial da fonte:

- `https://dadosabertos.camara.leg.br/swagger/api.html`
- Endpoint inicial: `https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome`

## Stack obrigatória

- Python 3.12 ou superior
- `uv`
- PostgreSQL 16
- SQLAlchemy 2
- Psycopg 3
- Alembic
- Pydantic e `pydantic-settings`
- HTTPX
- FastMCP ou SDK oficial do MCP
- Pytest
- Ruff
- Docker Compose

Não introduza frameworks ou infraestrutura fora do escopo, como FastAPI, Django, Redis, Celery, Airflow ou Kafka.

## Arquitetura de referência

Preserve a separação entre os dois aplicativos e o pacote compartilhado:

```text
public-data-mcp/
├── apps/
│   ├── extractor/
│   │   ├── cli.py
│   │   ├── client.py
│   │   ├── schemas.py
│   │   ├── transform.py
│   │   └── pipeline.py
│   └── mcp_server/
│       ├── server.py
│       ├── repositories.py
│       └── tools/
├── packages/
│   └── shared/
│       ├── config.py
│       ├── database.py
│       └── models.py
├── migrations/
├── tests/
├── docker/
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── pyproject.toml
├── .env.example
└── README.md
```

Pequenos ajustes são permitidos quando melhorarem objetivamente a implementação e forem documentados. Não misture responsabilidades entre extração, persistência e exposição via MCP.

## Responsabilidades por camada

### `apps/extractor`

- Cliente HTTP, paginação, timeout e retentativas limitadas.
- Validação Pydantic da resposta externa.
- Normalização dos dados antes da persistência.
- Orquestração da ingestão e contabilização dos resultados.
- CLI executável com `uv run python -m apps.extractor.cli sync`.

### `apps/mcp_server`

- Inicialização do servidor MCP via STDIO.
- Definição das cinco ferramentas públicas.
- Validação dos argumentos de cada ferramenta.
- Conversão de resultados e erros em respostas seguras para o cliente.
- Nenhuma consulta direta à API externa.

### `packages/shared`

- Configuração baseada em ambiente.
- Engine e sessões SQLAlchemy.
- Modelos persistidos e tipos compartilhados estáveis.
- Não concentrar regras específicas das ferramentas ou do pipeline neste pacote.

### `migrations`

- Fonte de verdade para o schema do banco.
- Criação e evolução de tabelas, índices, enums ou constraints.
- O aplicativo não deve criar o schema automaticamente em runtime.

## Fluxo de trabalho obrigatório

Antes de editar:

1. Inspecione os arquivos e o estado do Git.
2. Leia todos os arquivos `AGENTS.md` aplicáveis ao caminho alterado.
3. Preserve mudanças existentes e não relacionadas.
4. Apresente um plano curto quando a tarefa envolver implementação.

Durante a implementação:

1. Trabalhe em etapas pequenas e verificáveis.
2. Use type hints e funções com responsabilidades claras.
3. Atualize testes junto com o comportamento.
4. Registre suposições relevantes na documentação.
5. Não faça commits ou publique artefatos sem autorização explícita.
6. Não altere arquivos fora deste repositório.

Antes de concluir:

1. Execute os testes relevantes.
2. Execute o Ruff.
3. Para mudanças no fluxo completo, valide PostgreSQL, migrations, ingestão e MCP.
4. Relate exatamente o que foi ou não foi executado.
5. Nunca declare uma validação como concluída sem evidência da execução.

## Comandos de referência

Os comandos definitivos devem permanecer documentados no README. A interface esperada é:

```bash
uv sync
docker compose up -d postgres
uv run alembic upgrade head
uv run python -m apps.extractor.cli sync
uv run python -m apps.mcp_server.server
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Interface MCP obrigatória

O servidor deve expor exatamente as capacidades controladas abaixo, com nomes e descrições claras:

- `search_deputies`
- `get_deputy_by_id`
- `count_deputies_by_party`
- `count_deputies_by_state`
- `get_data_freshness`

Não exponha ferramentas genéricas de SQL, escrita, exclusão, execução de comandos ou acesso irrestrito ao banco.

## Critérios de aceite resumidos

Uma entrega só está pronta quando:

- O PostgreSQL inicia pelo Docker Compose e passa no healthcheck.
- As migrations são aplicadas com sucesso.
- A API é consumida com paginação, timeout, tratamento de erro e retentativas limitadas.
- Duas ingestões consecutivas não criam deputados duplicados.
- As execuções e suas métricas são registradas.
- O MCP inicia por STDIO e oferece as cinco ferramentas previstas.
- O MCP utiliza `mcp_readonly` e não oferece escrita ou SQL arbitrário.
- Os testes e o Ruff passam.
- O README permite a reprodução do ambiente por outra pessoa.

## Prioridades para decisões

Em caso de alternativas tecnicamente válidas, priorize nesta ordem:

1. Segurança e integridade dos dados.
2. Correção e comportamento determinístico.
3. Clareza arquitetural e facilidade de avaliação.
4. Testabilidade e rastreabilidade.
5. Simplicidade compatível com um MVP.
6. Desempenho proporcional ao pequeno volume esperado.

