🏛️ Sistema Jurídico - Gestão de Clientes
Sistema completo de gestão de clientes para escritórios jurídicos com suporte multi-escritórios, controle de permissões e auditoria.
📋 Características
✨ Funcionalidades Principais

Multi-escritórios: Cada escritório tem sua própria tabela dinâmica
Sistema de Usuários: 4 níveis de permissão (ADMIN, SUPERVISOR, OPERADOR, VISUALIZADOR)
CRUD Completo: Criar, editar, visualizar e excluir clientes
Soft Delete: Registros excluídos vão para tabela separada com opção de restauração
Busca Avançada: Por nome, CPF ou ID
Filtros por Data: Filtrar por data de fechamento ou protocolo
Paginação: Configurável (10, 20, 50, 100 registros por página)
Migração entre Escritórios: Individual ou em lote
Exportação: CSV e PDF
Auditoria Completa: Log de todas as operações
Gerenciamento de Escritórios: Criar, editar e excluir escritórios

🔐 Níveis de Permissão

ADMIN: Acesso total ao sistema
SUPERVISOR: Pode editar todos os escritórios e gerenciá-los
OPERADOR: Pode editar apenas escritórios atribuídos, visualiza todos
VISUALIZADOR: Apenas visualização de todos os escritórios

🚀 Instalação
Pré-requisitos

Python 3.8 ou superior
pip (gerenciador de pacotes Python)

Passo 1: Clone ou baixe o projeto
bashgit clone https://github.com/seu-usuario/sistema-juridico.git
cd sistema-juridico
Passo 2: Crie um ambiente virtual
bash# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
Passo 3: Instale as dependências
bashpip install -r requirements.txt
Passo 4: Execute o sistema
bashpython app.py
O sistema estará disponível em: http://localhost:5000
🔑 Acesso Padrão
Usuário: admin
Senha: admin

⚠️ IMPORTANTE: Altere a senha padrão após o primeiro acesso!

📁 Estrutura do Projeto
sistema-juridico/
├── app.py                      # Aplicação principal
├── requirements.txt            # Dependências
├── models/
│   └── models.py              # Modelos do banco de dados
├── routes/
│   ├── auth.py                # Rotas de autenticação
│   ├── clients.py             # Rotas de clientes
│   ├── admin.py               # Rotas administrativas
│   └── offices.py             # Rotas de escritórios
├── utils/
│   ├── audit.py               # Sistema de auditoria
│   ├── permissions.py         # Controle de permissões
│   └── offices.py             # Gerenciamento de escritórios
└── templates/
    ├── base.html              # Template base
    ├── auth/
    │   └── login.html         # Tela de login
    ├── clients/
    │   ├── list.html          # Lista de clientes
    │   ├── create.html        # Criar cliente
    │   ├── edit.html          # Editar cliente
    │   └── deleted.html       # Clientes excluídos
    ├── admin/
    │   ├── users.html         # Gerenciar usuários
    │   ├── user_create.html   # Criar usuário
    │   ├── user_edit.html     # Editar usuário
    │   └── audit.html         # Log de auditoria
    └── offices/
        ├── manage.html        # Gerenciar escritórios
        └── stats.html         # Estatísticas
📊 Banco de Dados
O sistema usa SQLite por padrão, criando o arquivo juridico.db automaticamente.
Tabelas Principais

users: Usuários do sistema
offices: Registro de escritórios
audit_logs: Log de auditoria
office_*: Tabelas dinâmicas para cada escritório
office_*_deleted: Tabelas de registros excluídos

Escritórios Padrão
O sistema cria 3 escritórios padrão:

central
campos
norte

🎯 Como Usar
1. Criar Novo Escritório

Acesse Gerenciar Escritórios
Digite o nome do escritório
Clique em Criar Escritório

O sistema cria automaticamente:

Código sanitizado (ex: "São Paulo" → "sao_paulo")
Tabela de registros (office_sao_paulo)
Tabela de excluídos (office_sao_paulo_deleted)

2. Cadastrar Cliente

Acesse Novo Cliente
Preencha o formulário:

Escritório: Digite o código (pode criar novo)
Nome e CPF: Obrigatórios
Demais campos: Opcionais


Clique em Cadastrar Cliente

3. Buscar e Filtrar
Na página Ver Registros:

Escritório: Selecione um específico ou "TODOS"
Buscar por: Nome, CPF ou ID
Filtro de Data: Por data de fechamento ou protocolo
Registros por página: 10, 20, 50 ou 100

4. Migrar Cliente
Individual:

Edite o cliente
Clique em Migrar
Digite o código do escritório de destino

Em Lote:

Selecione múltiplos clientes
Clique em Migrar Selecionados
Digite o código do escritório de destino

5. Excluir e Restaurar
Excluir:

Registros vão para tabela *_deleted
Mantém histórico completo

Restaurar:

Acesse Ver Excluídos
Selecione registros
Clique em Restaurar Selecionados

6. Exportar Dados
CSV: Formato tabela, compatível com Excel
PDF: Formato profissional para impressão
7. Gerenciar Usuários (Admin)

Acesse Usuários
Clique em Novo Usuário
Defina:

Username e senha
Papel (ADMIN, SUPERVISOR, OPERADOR, VISUALIZADOR)
Escritórios atribuídos (para OPERADOR)



🔧 Configurações Avançadas
Variáveis de Ambiente
Crie um arquivo .env:
envSECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=sqlite:///juridico.db
Deploy em Produção
Render.com

Crie conta no Render
Conecte o repositório GitHub
Configure:

Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app


Adicione variável de ambiente SECRET_KEY

Hostgator

Faça upload via FTP
Configure Python App no cPanel
Instale dependências
Configure passenger_wsgi.py

📈 Auditoria
O sistema registra automaticamente:

Logins e logouts
Criação, edição e exclusão de registros
Migrações entre escritórios
Alterações de usuários
Operações administrativas

Acesse: Auditoria (somente ADMIN)
🛡️ Segurança

Senhas criptografadas com Werkzeug
Controle de permissões por função
Sessões seguras com Flask-Login
Validação de entrada em todos os formulários
Proteção contra SQL Injection

🐛 Resolução de Problemas
Erro: "No module named 'flask'"
bashpip install -r requirements.txt
Erro: "Database is locked"
bash# Pare o servidor e reinicie
# No SQLite, apenas 1 processo pode escrever por vez
Templates não carregam
Verifique se a estrutura de pastas está correta:
templates/
├── base.html
├── auth/
├── clients/
├── admin/
└── offices/
📝 Notas Importantes

Backup Regular: Faça backup do arquivo juridico.db
Altere Senha Admin: Após primeira instalação
Escritórios: Nomes são convertidos automaticamente (espaços → underscores)
Permissões: OPERADOR só edita escritórios atribuídos
Soft Delete: Registros nunca são permanentemente excluídos

🔄 Atualizações Futuras

 Dashboard com gráficos
 Notificações por email
 API REST
 Aplicativo mobile
 Integração com assinatura digital
 Relatórios avançados

👥 Contribuindo

Fork o projeto
Crie uma branch (git checkout -b feature/nova-funcionalidade)
Commit suas mudanças (git commit -am 'Adiciona nova funcionalidade')
Push para a branch (git push origin feature/nova-funcionalidade)
Abra um Pull Request

📄 Licença
Este projeto é proprietário. Todos os direitos reservados.
💬 Suporte
Para dúvidas ou problemas:

Abra uma issue no GitHub
Entre em contato: suporte@exemplo.com


Desenvolvido com ❤️ seguindo as diretrizes do projeto
✅ Arquitetura modular
✅ Código limpo e organizado
✅ Sem refatorações grandes
✅ Evolução incremental
✅ 100% funcional desde V1
