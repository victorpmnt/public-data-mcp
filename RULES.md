# RULES.md

## Regras não negociáveis

### Escopo e dependências

1. Use Python 3.12 ou superior e `uv` para dependências e execução.
2. Use somente a stack definida em `AGENTS.md`, salvo necessidade técnica comprovada e documentada.
3. Não adicione FastAPI, Django, Redis, Celery, Airflow, Kafka ou serviços externos pagos.
4. Não use scraping. A única fonte de deputados é a API oficial da Câmara.
5. Preserve o escopo de MVP e evite abstrações sem uso concreto.

### Configuração e segredos

1. Toda configuração variável deve vir do ambiente por meio de `pydantic-settings`.
2. Nunca versione senhas, tokens, DSNs reais ou caminhos específicos da máquina.
3. O `.env.example` deve conter somente valores ilustrativos e seguros.
4. Não inclua credenciais, strings de conexão ou dados sensíveis em logs e mensagens de erro.
5. Falhe cedo e com mensagem clara quando uma configuração obrigatória estiver ausente ou inválida.

### Banco de dados

1. Use SQLAlchemy 2 com Psycopg 3.
2. Crie e altere o schema exclusivamente por migrations Alembic.
3. Não use `create_all()` como mecanismo de inicialização do ambiente.
4. `deputies.external_id` deve ser obrigatório e único.
5. O upsert deve usar `external_id` como chave de idempotência.
6. Crie índices para nome, partido, estado e a combinação partido/estado.
7. Restrinja o status de `ingestion_runs` por enum ou constraint equivalente.
8. Mantenha três papéis separados:
   - usuário administrativo para migrations;
   - `extractor_user` para leitura e escrita necessárias à ingestão;
   - `mcp_readonly` somente para `SELECT` nas tabelas necessárias.
9. O servidor MCP deve usar obrigatoriamente a conexão de `mcp_readonly`.
10. Consultas devem ser parametrizadas por construção; nunca monte SQL com entrada do usuário.

### Extrator

1. O comando público da ingestão é `uv run python -m apps.extractor.cli sync`.
2. Registre o início da execução antes de acessar a fonte externa.
3. Percorra a paginação indicada pela resposta da API; não presuma uma página única.
4. Configure timeout explícito no HTTPX.
5. Trate respostas HTTP inválidas e implemente apenas retentativas limitadas para falhas transitórias.
6. Não faça retentativa indiscriminada de erros permanentes.
7. Valide os dados externos com Pydantic antes da persistência.
8. Normalize espaços, nomes, siglas de partido e UF e campos opcionais.
9. Registros inválidos devem ser contabilizados como rejeitados e gerar log contextual seguro.
10. Não interrompa toda a ingestão por um registro individual inválido quando for seguro rejeitá-lo.
11. Erros fatais devem marcar a execução como falha e preencher `error_message` de forma sanitizada.
12. Ao final, imprima um resumo legível com recebidos, inseridos, atualizados e rejeitados.
13. Uma segunda execução com os mesmos dados não pode duplicar deputados.

### MCP

1. Use transporte STDIO.
2. O servidor consulta apenas o PostgreSQL; ele nunca acessa a API da Câmara.
3. Exponha somente:
   - `search_deputies`;
   - `get_deputy_by_id`;
   - `count_deputies_by_party`;
   - `count_deputies_by_state`;
   - `get_data_freshness`.
4. Valide todos os argumentos de ferramenta.
5. Normalize partido e estado para letras maiúsculas.
6. A busca por nome deve ser parcial e case-insensitive.
7. `search_deputies` deve ter limite padrão, limite máximo de 100 e offset não negativo.
8. Ordene buscas e agregações deterministicamente, incluindo critério de desempate.
9. `get_deputy_by_id` recebe o `external_id` oficial, não a chave interna.
10. Retorne mensagens claras para registros inexistentes e erros públicos seguros para falhas internas.
11. Nunca exponha SQL arbitrário, fragmentos SQL, operações de escrita ou detalhes internos da conexão.

### Observabilidade

1. Use logs consistentes e legíveis; prefira campos estruturados quando isso não aumentar muito a complexidade.
2. Inclua contexto operacional como execução, página e `external_id` quando disponível.
3. Nunca registre segredos ou a resposta integral quando ela puder conter dados desnecessários.
4. Não silencie exceções. Capture apenas quando puder registrar, traduzir ou recuperar corretamente.

### Testes

1. Testes unitários não podem depender da disponibilidade da API oficial.
2. Simule respostas HTTP, paginação, falhas transitórias e erros permanentes.
3. Cubra validação, rejeição, normalização, paginação, erro HTTP e idempotência do extrator.
4. Cubra filtros isolados e combinados, paginação, limite máximo, ausência de deputado, agregações e freshness no MCP.
5. Verifique explicitamente que nenhuma ferramenta de escrita ou SQL arbitrário está registrada.
6. Inclua ao menos um teste de integração reproduzível com PostgreSQL, se o ambiente Docker estiver disponível.
7. Testes devem verificar comportamento e efeitos observáveis, não detalhes internos frágeis.
8. Não reduza validações ou remova testes apenas para fazer a suíte passar.

### Qualidade de código

1. Use type hints nas interfaces e funções do projeto.
2. Prefira funções pequenas, nomes descritivos e dependências explícitas.
3. Separe acesso ao banco, regras de aplicação e adaptação MCP.
4. Evite duplicação, código morto, placeholders sem propósito e comentários redundantes.
5. Comentários devem explicar decisões não evidentes, não repetir o código.
6. Siga a configuração do Ruff para lint e formatação.
7. Mantenha comportamento síncrono ou assíncrono consistente dentro de cada fluxo.

### Mudanças no repositório

1. Inspecione o estado atual antes de editar.
2. Preserve alterações do usuário e trabalhos não relacionados.
3. Não modifique arquivos fora da raiz do projeto.
4. Não faça commit, push, publicação ou deploy sem autorização explícita.
5. Não execute ações destrutivas sem confirmar o alvo e a autorização.
6. Pequenas decisões reversíveis podem ser tomadas sem interromper o trabalho; documente suposições relevantes.

### Documentação e entrega

1. O README deve ensinar todo o fluxo partindo de uma máquina sem configuração prévia do projeto.
2. Use placeholders portáveis em exemplos de configuração MCP.
3. Inclua um diagrama Mermaid da arquitetura.
4. Documente ferramentas, segurança, testes, limitações e evoluções possíveis.
5. Só afirme que um comando ou integração funciona se ele tiver sido executado no ambiente correspondente.
6. Na entrega, diferencie claramente validações executadas, não executadas e eventuais pendências.

