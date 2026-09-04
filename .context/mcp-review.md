# Revisão do serviço MCP

## Resumo

O desenho do serviço está adequado para um MVP de case júnior: o servidor usa o SDK oficial MCP v2, transporte STDIO, registra exatamente cinco ferramentas e concentra o acesso ao banco em um repositório de consultas. A separação entre servidor, ferramentas e `packages/shared` é clara e não há acesso à API externa no MCP.

Foi encontrado um problema funcional importante no repositório: consultas que usam `select(Deputy)` ou `select(IngestionRun)` combinadas com `.mappings()` tentam acessar chaves de coluna que não existem no resultado ORM. Isso quebra `search_deputies`, `get_deputy_by_id` e `get_data_freshness` quando há dados (e, no freshness, quando há execuções). A correção é simples: selecionar explicitamente as colunas necessárias ou usar entidades ORM via `scalars()`.

## Pontos corretos

- `create_server()` registra somente `search_deputies`, `get_deputy_by_id`, `count_deputies_by_party`, `count_deputies_by_state` e `get_data_freshness`.
- O servidor cria a conexão por `create_mcp_engine(settings)`, portanto usa a URL configurada para `mcp_readonly`.
- O transporte usado é `run_stdio_async()`, compatível com o SDK MCP v2.1.1 fixado no lockfile. A API v2 documenta `MCPServer` e STDIO como caminhos suportados.
- Filtros do repositório são construídos com SQLAlchemy, sem SQL concatenado ou SQL arbitrário.
- Todas as consultas de deputados filtram `is_active = true`.
- Busca por nome usa `ILIKE`, e partido/UF são normalizados para maiúsculas no repositório.
- Busca e agregações possuem ordenação determinística; `search` aplica limite e offset.
- Os validadores rejeitam limite fora de 1..100, offset negativo, ID não positivo e UF que não tenha duas letras.
- `_safe_call` preserva erros de validação e converte falhas internas em mensagem pública genérica, registrando a exceção no log.
- Índices necessários para nome, partido, estado e partido/estado existem no modelo e na migration.

## Problemas reais

### Alta — resultados ORM tratados como mapeamentos de colunas

Em `apps/mcp_server/repositories.py`, `search()` e `get_by_external_id()` fazem `select(Deputy).mappings()` e depois acessam `row["external_id"]`, `row["name"]`, etc. Um `select()` de uma entidade ORM retorna um mapeamento com a chave da entidade (`Deputy`), não com cada coluna. Com dados, essas funções devem levantar `KeyError` antes de responder ao cliente.

`freshness()` repete o mesmo padrão com `select(IngestionRun).mappings()` e acessos como `latest["source"]`; também falha quando existe uma execução.

Correção simples: trocar os selects por `select(Deputy.external_id, Deputy.name, ...)` e manter `.mappings()`, ou usar `select(Deputy)` com `.scalars()` e ler atributos do objeto. Selecionar colunas explícitas deixa o contrato de resposta mais visível e é a opção recomendada para este MVP.

### Média — cobertura de testes insuficiente para detectar o problema

`tests/mcp_server/test_tools.py` testa apenas o limite da busca e o caso de deputado inexistente usando um fake repository. `test_server.py` testa somente os nomes registrados. Não há testes do `DeputyRepository`, das respostas com dados, dos filtros, paginação, agregações, freshness, erro interno ou da conexão read-only. O bug acima passa despercebido porque nenhum teste executa os selects reais.

### Baixa — validação dos filtros de agregação é assimétrica

`count_deputies_by_party` valida a UF, mas `count_deputies_by_state` não valida o partido; a validação é parcialmente compensada pela normalização no repositório. Para um contrato consistente, validar partido como string não vazia e sigla em maiúsculas (ou documentar que partido aceita texto livre). Também seria útil normalizar os valores antes de passá-los ao repositório, embora o comportamento atual já normalize no ponto de consulta.

### Baixa — configuração de limite não é utilizada

`Settings` possui `mcp_default_limit` e `mcp_max_limit`, mas `search_deputies` e o wrapper MCP usam os literais 20 e 100. Não quebra o comportamento atual, porém torna essas configurações inefetivas. Para manter simplicidade, pode-se remover essas duas configurações e assumir os limites documentados; alternativamente, passar `Settings` ao construtor do servidor.

## Validações executadas

- Inspeção estática de todos os arquivos de `apps/mcp_server`, `packages/shared`, `tests/mcp_server`, migration, Docker Compose e documentação.
- Ruff check no escopo MCP/shared/testes: passou (`All checks passed!`).
- Ruff format check no escopo MCP/shared/testes: passou (`16 files already formatted`).
- Não foi possível executar Pytest: o Python do `.venv` aponta para um executável da Microsoft Store indisponível nesta sessão (`Unable to create process...`).
- Não foi possível validar PostgreSQL, privilégios ou chamadas MCP contra banco real: o daemon Docker não aceitou conexão (`permission denied while trying to connect to the Docker API`).
- A compatibilidade de `MCPServer`, `run_stdio_async()` e dos argumentos do construtor foi conferida na documentação/código oficial do SDK v2; o lockfile registra `mcp 2.1.1`.

## Plano técnico simples e priorizado

1. **Corrigir o bloqueio funcional (alta prioridade).** Alterar apenas os selects de `DeputyRepository` para selecionar colunas explícitas (incluindo os campos retornados) e ajustar freshness para selecionar as colunas de `IngestionRun` explicitamente. Manter a estrutura atual, sem criar camadas novas.
2. **Adicionar testes de repositório (alta prioridade).** Com SQLite em memória para a parte SQL compatível, ou PostgreSQL do Compose para integração, cobrir busca com dados, deputado por ID, freshness com execução, agregações, filtros combinados e apenas ativos. Um teste de cada método já captura a regressão principal; PostgreSQL deve ser usado para confirmar `ILIKE` e tipos reais.
3. **Adicionar teste de segurança/registro (média prioridade).** Manter o teste existente das cinco ferramentas e acrescentar uma verificação de que não há ferramentas extras. No ambiente Docker, testar `SELECT` permitido e `INSERT/UPDATE/DELETE` negados para `mcp_readonly`.
4. **Harmonizar validações e configuração (baixa prioridade).** Validar partido no wrapper de agregação, ou registrar explicitamente a decisão de aceitar texto livre. Usar as configurações de limite ou removê-las para não sugerir que são ajustáveis.
5. **Validar o fluxo final.** Com Docker e um Python/uv funcional: aplicar migration, executar ingestão, iniciar o MCP via STDIO e chamar as cinco ferramentas, registrando resultados no README.

## Decisão de escopo

Não recomendo adicionar autenticação de rede, async SQLAlchemy, camada de services/repositories genérica, paginação MCP customizada ou framework web. Para o volume do case, as correções acima resolvem o comportamento e aumentam muito a confiança sem tornar o projeto complexo.
