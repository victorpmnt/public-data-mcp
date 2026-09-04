# Revisão técnica do serviço extractor

## Escopo

Revisão estática do cliente HTTP, schemas Pydantic, normalização, pipeline de ingestão, modelos compartilhados relacionados e testes do extractor. O objetivo foi avaliar o comportamento do MVP para um case de vaga júnior, priorizando clareza e correções pequenas.

## Resumo

O extractor está bem dividido em cliente, validação, normalização e pipeline. A implementação já cobre o fluxo principal: paginação por `rel=next`, timeout explícito, retries limitados, rejeição de registros inválidos, upsert por `external_id`, reativação de deputados e inativação de ausentes após uma coleta completa.

Não identifiquei uma falha no caminho normal que impeça o MVP de funcionar. Há, porém, um caso real de duplicidade dentro da própria resposta da API que pode causar erro de constraint e derrubar a ingestão. A cobertura de testes ainda é pequena para declarar o extractor validado: faltam testes de retries, erros HTTP, JSON/schema inválido, falha fatal e reconciliação de `is_active`.

## Pontos corretos

- `CâmaraClient` usa HTTPX com timeout de conexão, leitura, escrita e pool definidos.
- O cliente segue o link `rel=next` retornado pela API e possui limite de segurança de páginas.
- Retries estão limitados a falhas transitórias (`429`, `5xx` selecionados, timeout e falhas de rede). Erros HTTP permanentes não são repetidos.
- `ApiPage` e `ApiDeputy` toleram campos extras da API, reduzindo acoplamento desnecessário.
- O identificador externo é validado como inteiro positivo; URLs são validadas com `HttpUrl`.
- `normalize_deputy` é uma função pura, pequena e fácil de testar. Ela limpa espaços, converte partido/UF para maiúsculas, transforma vazio em `None` e rejeita nome, partido ou UF inválidos.
- O pipeline registra `running` antes da chamada HTTP e atualiza a execução para `succeeded` ou `failed`.
- A persistência só ocorre depois que todas as páginas foram lidas. Assim, uma falha de paginação não deixa uma carga parcial no banco.
- O upsert usa `external_id` como chave lógica e não conta como atualização quando os campos persistidos não mudaram.
- Deputados presentes são reativados e os ausentes são marcados como inativos apenas depois do processamento completo.
- A transação de persistência é delimitada por `session_scope`, com commit e rollback explícitos.
- O resumo da CLI informa recebidos, inseridos, atualizados e rejeitados.

## Problemas reais

### P1 — IDs duplicados na mesma coleta podem causar `UNIQUE violation`

Local: `apps/extractor/pipeline.py`, função `_upsert`, aproximadamente linhas 44–65.

`existing_rows` é carregado uma vez antes do loop. Se duas páginas ou dois itens da mesma página contiverem o mesmo `external_id`, os dois itens encontram `row is None`, são adicionados como novos e o flush pode falhar na constraint única. A API normalmente não deve repetir deputados, mas a ingestão precisa lidar com resposta externa inconsistente sem uma falha pouco explicável.

Plano simples: deduplicar os itens válidos por `external_id` antes de `_upsert` ou, ainda mais explicitamente, manter um `seen_external_ids` no pipeline e ignorar duplicatas posteriores. A métrica deve contar o registro lógico uma vez. Adicionar um teste unitário para duas ocorrências do mesmo ID.

### P2 — `error_message` pode armazenar exceção interna sem sanitização

Local: `apps/extractor/pipeline.py`, aproximadamente linhas 121–130.

Em falhas fatais, `run.error_message = str(exc)[:1000]` grava a mensagem original. Erros de banco, configuração ou driver podem conter detalhes internos, nomes de host ou informações de conexão. Isso contraria a regra de não expor detalhes sensíveis e torna o histórico menos seguro.

Plano simples: para erros conhecidos (`CâmaraApiError`, validação etc.), salvar a mensagem segura; para exceções inesperadas, salvar uma mensagem genérica como `falha interna durante a ingestão` e manter o traceback somente no log. Não é necessário criar uma hierarquia complexa de exceções.

### P2 — Testes não cobrem as garantias principais do extractor

Os testes existentes cobrem apenas uma paginação feliz, limpeza/UF inválida e um upsert básico em SQLite. Não há testes para:

- retry de timeout, `429` e `5xx`, nem ausência de retry para `4xx` permanentes;
- JSON inválido, payload que não é objeto ou página inválida;
- limite de páginas e links `next` inválidos;
- rejeição de `ApiDeputy.model_validate` dentro do pipeline;
- marcação de registros ausentes como inativos e reativação;
- falha durante a coleta e atualização de `ingestion_runs` para `failed`;
- métricas de inseridos/atualizados/rejeitados;
- duplicidade do mesmo `external_id`.

Plano simples: adicionar testes unitários com `httpx.MockTransport` e SQLite apenas para comportamentos puros/CRUD simples. Um teste de integração PostgreSQL deve permanecer separado para validar enum, migrations e permissões; não é necessário introduzir Testcontainers.

### P3 — Retries usam `time.sleep` fixo e ignoram `Retry-After`

Local: `apps/extractor/client.py`, aproximadamente linhas 44–73.

O backoff exponencial limitado funciona para o MVP, mas bloqueia o processo durante testes e não aproveita `Retry-After` em respostas `429`. Não é uma falha funcional grave, e a simplicidade atual é aceitável.

Plano: manter o backoff simples. Opcionalmente extrair a espera para uma função pequena injetável nos testes, ou apenas monkeypatchar `time.sleep`. Não vale adicionar biblioteca de retry. Tratar `Retry-After` só se surgir como requisito explícito.

## Pontos para confirmar, mas não bloqueadores

- `source_updated_at` existe no model, mas não é preenchido porque a listagem atual não fornece uma data confiável. Isso está documentado e é uma decisão adequada para o MVP.
- Uma coleta com somente registros inválidos não desativa os deputados existentes, pois a reconciliação só ocorre quando há IDs válidos. É uma proteção razoável contra uma resposta externa totalmente inválida.
- Uma resposta vazia também não desativa todos os registros existentes. Para o case, é uma salvaguarda aceitável; deve ser mencionada como decisão no README se o comportamento for mantido.
- O cliente usa `HttpUrl` para links, mas não verifica que cada URL tenha domínio oficial da Câmara. Como os links vêm da API oficial e não são entrada do usuário, essa validação não é necessária para o MVP.
- O teste de upsert usa `Base.metadata.create_all` e SQLite. Isso é adequado para teste unitário rápido, mas não substitui a validação real no PostgreSQL.

## Validações executadas

- Inspeção dos arquivos de implementação e testes do extractor e do pacote compartilhado relacionado.
- Leitura de `AGENTS.md`, `RULES.md` e `SKILLS.md`.
- Tentativa de executar `uv run pytest tests/extractor -q`.
- Tentativa de executar `uv run ruff check apps/extractor packages/shared tests/extractor`.
- Tentativa de executar `uv run ruff format --check apps/extractor packages/shared tests/extractor`.

As três tentativas de comando não foram executadas porque o executável `uv` não está disponível no `PATH` deste ambiente (`uv: The term 'uv' is not recognized`). Portanto, não há evidência nova de testes ou lint nesta revisão.

## Plano técnico priorizado

1. Corrigir deduplicação por `external_id` antes do upsert e adicionar teste correspondente.
2. Sanitizar a mensagem persistida em `ingestion_runs.error_message` para exceções inesperadas.
3. Expandir os testes unitários do cliente para retries, erros permanentes, JSON inválido e limite de paginação.
4. Expandir testes do pipeline para rejeição, métricas, inativação/reativação, falha e idempotência.
5. Rodar a suíte completa, Ruff e, com Docker disponível, migration + uma ingestão real + segunda ingestão para demonstrar idempotência.

## Recomendação

O extractor pode seguir para uma rodada curta de correções e testes. Não recomendo introduzir async, repository genérico, biblioteca de retry, filas ou uma camada adicional de domínio: o código atual já tem separação suficiente para o case e as melhorias acima resolvem os riscos relevantes com poucas mudanças.
