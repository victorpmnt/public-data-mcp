# Guia de comandos

Execute os comandos a partir da raiz do projeto:

```powershell
cd D:\programacao\data_extractor
```

## Configuração

Instalar dependências:

```powershell
uv sync
```

Se `uv` não estiver no `PATH`:

```powershell
python -m uv sync
```

Criar o ambiente local:

```powershell
Copy-Item .env.example .env
```

No ambiente atual, use `DB_PORT=5433`, pois a porta `5432` está ocupada por outro PostgreSQL local. Não versionar nem compartilhar o `.env`.

## Docker e PostgreSQL

```powershell
docker info
docker compose up -d postgres
docker compose ps
docker compose logs postgres --tail 100
```

Logs contínuos:

```powershell
docker compose logs -f postgres
```

Parar sem apagar dados:

```powershell
docker compose stop postgres
docker compose start postgres
```

Remover container e rede, preservando volume:

```powershell
docker compose down
```

Remover também o volume — **apaga todos os dados do banco**:

```powershell
docker compose down -v
```

Use `down -v` somente em ambiente descartável.

## Migrations

Aplicar o schema:

```powershell
uv run alembic upgrade head
```

Alternativa:

```powershell
python -m uv run alembic upgrade head
```

Consultar estado e histórico:

```powershell
uv run alembic current
uv run alembic history
```

Gerar SQL sem executar:

```powershell
uv run alembic upgrade head --sql
```

O schema deve ser alterado somente por migrations Alembic, nunca manualmente no pgAdmin.

## Extrator

Executar sincronização:

```powershell
uv run python -m apps.extractor.cli sync
```

Alternativa:

```powershell
python -m uv run python -m apps.extractor.cli sync
```

Execute duas vezes para verificar idempotência. Na segunda execução, esperamos normalmente `inseridos=0` e `atualizados=0`.

## Consultas SQL

Abrir `psql` no container:

```powershell
docker compose exec postgres psql -h 127.0.0.1 -U postgres_admin -d public_data -W
```

Sair do `psql`:

```sql
\q
```

Consultas úteis:

```sql
SELECT COUNT(*) FROM deputies;
SELECT COUNT(*) FROM deputies WHERE is_active = true;
SELECT * FROM ingestion_runs ORDER BY started_at DESC;
```

No pgAdmin, use `localhost:5433`, database `public_data` e o usuário administrativo do `.env`.

## Testes e qualidade

```powershell
uv run pytest
uv run pytest tests/extractor -q
uv run pytest tests/mcp_server -q
uv run pytest --cov=apps --cov=packages
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall -q apps packages migrations
```

Correções automáticas de estilo:

```powershell
uv run ruff check --fix .
uv run ruff format .
```

## MCP

Iniciar por STDIO:

```powershell
uv run python -m apps.mcp_server.server
```

O processo ficará aguardando mensagens do cliente MCP. Isso é esperado; ele não é uma API HTTP.

Ferramentas disponíveis:

- `search_deputies`
- `get_deputy_by_id`
- `count_deputies_by_party`
- `count_deputies_by_state`
- `get_data_freshness`

Configuração de exemplo:

```json
{
  "mcpServers": {
    "public-data-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "apps.mcp_server.server"],
      "cwd": "<CAMINHO_DO_PROJETO>"
    }
  }
}
```

## Diagnóstico rápido

### `uv` não é reconhecido

```powershell
python -m pip install --user uv
python -m uv --version
```

Abra um novo PowerShell para disponibilizar o executável `uv` no `PATH`.

### Falha de autenticação

Confira `DB_PORT=5433`, `DB_ADMIN_USER`, `DB_ADMIN_PASSWORD` e o status:

```powershell
docker compose ps
docker compose logs postgres --tail 100
```

### Porta ocupada

```powershell
Get-NetTCPConnection -LocalPort 5432 -State Listen
Get-NetTCPConnection -LocalPort 5433 -State Listen
```

### Docker indisponível

Inicie o Docker Desktop e aguarde o status operacional. Depois rode `docker info` novamente.

## Segurança

- Não compartilhe senhas do `.env`.
- Não use `mcp_readonly` para migrations ou ingestão.
- Não execute `docker compose down -v` com dados importantes.
- Não use SQL arbitrário no MCP.

## Dockerfile

Construir a imagem da aplicação:

```powershell
docker build -t public-data-mcp:local .
```

O Compose deste MVP inicia o PostgreSQL; o servidor MCP pode ser executado localmente com `uv`.

## Fluxo completo

```powershell
uv sync
docker compose up -d postgres
docker compose ps
uv run alembic upgrade head
uv run python -m apps.extractor.cli sync
uv run python -m apps.extractor.cli sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python -m apps.mcp_server.server
```
