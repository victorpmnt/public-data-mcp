# SKILLS.md

## Finalidade

Este arquivo mapeia as competências necessárias para implementar e revisar o projeto. Ele não adiciona dependências nem substitui `AGENTS.md` e `RULES.md`; serve como guia para escolher a abordagem adequada em cada tarefa.

## 1. Arquitetura Python de monorepo

Aplicar quando criar ou reorganizar módulos, dependências internas e pontos de entrada.

Competências esperadas:

- Estruturar `apps` e `packages` como pacotes importáveis.
- Separar aplicação, domínio simples, persistência e adaptadores externos.
- Configurar `pyproject.toml` para Python 3.12+, `uv`, Pytest e Ruff.
- Evitar ciclos de importação e pacotes compartilhados excessivamente genéricos.
- Criar CLIs e módulos executáveis com `python -m`.

Resultado esperado: os aplicativos podem evoluir e ser testados separadamente, compartilhando apenas configuração, banco e modelos estáveis.

## 2. Integração HTTP resiliente

Aplicar no cliente da API oficial da Câmara.

Competências esperadas:

- Usar HTTPX com timeout explícito.
- Tratar códigos HTTP e falhas de transporte de maneira distinta.
- Implementar retentativas limitadas com backoff simples para falhas transitórias.
- Interpretar os links de paginação fornecidos pela API.
- Tornar o cliente substituível ou injetável para testes.
- Evitar loops infinitos de paginação e retentativa.

Resultado esperado: todas as páginas são obtidas ou a execução falha de forma rastreável e segura.

## 3. Modelagem e validação com Pydantic

Aplicar nas configurações, entradas externas e argumentos das ferramentas.

Competências esperadas:

- Modelar somente os campos necessários, tolerando extensões compatíveis da API.
- Validar identificadores, URLs, siglas, limites e offsets.
- Diferenciar campo ausente, valor nulo e string vazia quando isso afetar persistência.
- Usar `pydantic-settings` para configurações derivadas do ambiente.
- Produzir mensagens úteis sem revelar valores sensíveis.

Resultado esperado: dados inválidos são identificados antes de atingir o banco e configurações incorretas falham cedo.

## 4. Normalização de dados

Aplicar entre a validação externa e o upsert.

Competências esperadas:

- Remover espaços externos e normalizar espaços repetidos quando apropriado.
- Converter partido e UF para maiúsculas.
- Converter strings vazias em `None` para campos opcionais.
- Preservar nomes e identificadores oficiais sem transformações destrutivas.
- Manter funções puras para facilitar testes unitários.

Resultado esperado: consultas consistentes e atualizações idempotentes, sem perda de significado dos dados de origem.

## 5. PostgreSQL, SQLAlchemy 2 e Psycopg 3

Aplicar na modelagem, persistência e consultas MCP.

Competências esperadas:

- Mapear modelos com a API tipada do SQLAlchemy 2.
- Gerenciar transações e sessões explicitamente.
- Implementar upsert PostgreSQL por `external_id`.
- Distinguir inserções de atualizações para métricas corretas.
- Criar consultas parametrizadas, filtros opcionais e agregações.
- Selecionar índices coerentes com os padrões de busca.
- Evitar N+1, transações longas e vazamento de conexões.

Resultado esperado: carga atômica no nível apropriado, métricas confiáveis e consultas determinísticas.

## 6. Migrations com Alembic

Aplicar em toda mudança de schema.

Competências esperadas:

- Criar revisões reproduzíveis com `upgrade` e `downgrade` coerentes.
- Definir tabelas, constraints, índices, timestamps e status de ingestão.
- Revisar migrations autogeradas antes de aceitá-las.
- Validar a aplicação a partir de um banco vazio.
- Não misturar concessão de privilégios dependente do ambiente com lógica obscura de runtime.

Resultado esperado: qualquer avaliador consegue reconstruir o schema apenas com Alembic e a configuração documentada.

## 7. Segurança e privilégios PostgreSQL

Aplicar na inicialização Docker, configuração de conexões e revisão do MCP.

Competências esperadas:

- Aplicar princípio do menor privilégio.
- Separar credenciais administrativas, de ingestão e de leitura.
- Conceder ao `mcp_readonly` apenas os `SELECT` necessários.
- Configurar privilégios padrão quando migrations futuras criarem objetos.
- Verificar permissões com tentativas positivas de leitura e negativas de escrita.
- Sanitizar erros antes de retorná-los ao cliente MCP.

Resultado esperado: uma falha ou entrada maliciosa no MCP não oferece caminho de escrita no banco.

## 8. Desenvolvimento de servidor MCP

Aplicar no registro, descrição e execução das ferramentas via STDIO.

Competências esperadas:

- Inicializar FastMCP ou o SDK oficial sem servidor HTTP adicional.
- Escrever descrições que permitam ao agente escolher corretamente cada ferramenta.
- Definir schemas de entrada restritos e retornos serializáveis.
- Manter ferramentas finas, delegando consultas a repositórios.
- Evitar qualquer saída de log em `stdout` que corrompa o protocolo STDIO; direcionar logs conforme suporte da implementação.
- Inspecionar as ferramentas registradas em testes.

Resultado esperado: clientes como Codex e Claude Desktop conseguem descobrir e invocar somente as cinco consultas autorizadas.

## 9. Testes com Pytest

Aplicar junto de cada comportamento implementado.

Competências esperadas:

- Usar fixtures pequenas e factories de dados legíveis.
- Simular HTTP sem acesso à rede.
- Testar paginação com múltiplas páginas e término correto.
- Testar transações, upsert e idempotência em PostgreSQL.
- Testar repositórios separadamente da camada MCP quando isso melhorar o diagnóstico.
- Validar limites, normalizações, ordenação e mensagens de ausência.
- Marcar e documentar testes de integração que exigem Docker.

Resultado esperado: a suíte detecta regressões relevantes e continua rápida no ciclo local.

## 10. Docker e operação local

Aplicar ao ambiente PostgreSQL e à demonstração do case.

Competências esperadas:

- Criar serviço `postgres` compatível com PostgreSQL 16.
- Configurar volume persistente, healthcheck e variáveis de ambiente.
- Inicializar papéis e permissões de maneira reproduzível.
- Evitar dependência em ordem temporal frágil; usar healthchecks e comandos explícitos.
- Documentar como recriar o ambiente e diagnosticar falhas comuns.

Resultado esperado: `docker compose up -d postgres` disponibiliza um banco saudável para migrations, ingestão e testes.

## 11. Observabilidade e rastreabilidade

Aplicar no pipeline, cliente HTTP e fronteiras do MCP.

Competências esperadas:

- Produzir logs consistentes com evento, severidade e contexto.
- Registrar métricas de recebidos, inseridos, atualizados e rejeitados.
- Garantir atualização de `ingestion_runs` tanto no sucesso quanto na falha.
- Preservar a exceção original internamente sem expor detalhes sensíveis externamente.
- Tornar o resumo da CLI adequado para uma demonstração técnica.

Resultado esperado: é possível explicar o que ocorreu em cada ingestão sem reproduzir o problema manualmente.

## 12. Documentação técnica

Aplicar continuamente e consolidar antes da entrega.

Competências esperadas:

- Escrever instruções executáveis e na ordem correta.
- Explicar arquitetura e decisões sem transformar o README em especificação duplicada.
- Criar diagrama Mermaid claro.
- Fornecer exemplos portáveis de configuração MCP para Codex e Claude Desktop.
- Documentar limitações reais e evoluções possíveis.
- Registrar resultados de verificação sem exagerar garantias.

Resultado esperado: outra pessoa consegue instalar, executar, testar e demonstrar o projeto sem conhecimento prévio.

## Matriz rápida de aplicação

| Tarefa | Competências principais |
| --- | --- |
| Criar estrutura inicial | Arquitetura Python, documentação técnica |
| Implementar configurações | Pydantic, segurança de segredos |
| Criar models e migrations | SQLAlchemy, PostgreSQL, Alembic |
| Implementar ingestão | HTTPX, Pydantic, normalização, observabilidade |
| Implementar ferramentas MCP | MCP, SQLAlchemy, validação, segurança |
| Configurar Docker | Docker, PostgreSQL, privilégios |
| Criar a suíte de testes | Pytest, HTTP simulado, integração PostgreSQL |
| Fazer verificação final | Operação local, segurança, documentação |

## Referências que devem orientar decisões

Quando uma decisão depender do comportamento de uma ferramenta ou biblioteca, consulte primeiro a documentação oficial correspondente:

- API de Dados Abertos da Câmara dos Deputados
- Python
- `uv`
- SQLAlchemy 2
- Psycopg 3
- Alembic
- Pydantic
- HTTPX
- Model Context Protocol e FastMCP
- PostgreSQL 16
- Pytest
- Ruff
- Docker Compose

Evite basear decisões críticas apenas em memória, exemplos não oficiais ou APIs obsoletas.
