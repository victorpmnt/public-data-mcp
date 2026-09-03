-- Executado pelo usuário administrativo apenas na criação inicial do volume.
CREATE ROLE extractor_user LOGIN PASSWORD :'extractor_password';
CREATE ROLE mcp_readonly LOGIN PASSWORD :'mcp_password';

GRANT CONNECT ON DATABASE :"db_name" TO extractor_user, mcp_readonly;
GRANT USAGE ON SCHEMA public TO extractor_user, mcp_readonly;

-- As tabelas serão criadas pelas migrations. Estes privilégios garantem que
-- o extrator tenha a escrita necessária e o MCP permaneça somente leitura.
ALTER DEFAULT PRIVILEGES FOR ROLE :"admin_user" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE ON TABLES TO extractor_user;
ALTER DEFAULT PRIVILEGES FOR ROLE :"admin_user" IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO extractor_user;
ALTER DEFAULT PRIVILEGES FOR ROLE :"admin_user" IN SCHEMA public
  GRANT SELECT ON TABLES TO mcp_readonly;
