from flask import Flask, redirect, url_for
from flask_login import LoginManager
import os
from datetime import timedelta

# Importar models
from models.models import db, User

# Importar blueprints
from routes.auth import auth_bp
from routes.clients import clients_bp
from routes.admin import admin_bp
from routes.offices import offices_bp

def create_app():
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///juridico.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Inicializar extensões
    db.init_app(app)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(offices_bp)
    
    # Rota raiz
    @app.route('/')
    def index():
        return redirect(url_for('clients.list_clients'))
    
    # Criar tabelas e admin padrão
    with app.app_context():
        db.create_all()
        create_default_admin()
        create_default_offices()
    
    return app

def create_default_admin():
    """Cria usuário admin padrão se não existir"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            nome='Administrador',
            role='ADMIN',
            ativo=True
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário admin criado (username: admin, senha: admin)")

def create_default_offices():
    """Cria tabelas de escritórios padrão se não existirem"""
    from sqlalchemy import text
    
    default_offices = ['central', 'campos', 'norte']
    
    for office in default_offices:
        table_name = f'office_{office}'
        
        # Verificar se a tabela já existe
        query = text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        result = db.session.execute(query).fetchone()
        
        if not result:
            # Criar tabela do escritório
            create_table_query = text(f"""
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cpf TEXT NOT NULL,
                    tipo_acao TEXT,
                    data_fechamento DATE,
                    pendencias TEXT,
                    numero_processo TEXT,
                    data_protocolo DATE,
                    observacoes TEXT,
                    captador_pago TEXT,
                    nome_captador TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_by INTEGER
                )
            """)
            db.session.execute(create_table_query)
            
            # Criar tabela de excluídos
            create_deleted_query = text(f"""
                CREATE TABLE {table_name}_deleted (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_id INTEGER,
                    nome TEXT,
                    cpf TEXT,
                    tipo_acao TEXT,
                    data_fechamento DATE,
                    pendencias TEXT,
                    numero_processo TEXT,
                    data_protocolo DATE,
                    observacoes TEXT,
                    captador_pago TEXT,
                    nome_captador TEXT,
                    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_by INTEGER,
                    original_created_at TIMESTAMP,
                    original_updated_at TIMESTAMP
                )
            """)
            db.session.execute(create_deleted_query)
            
            db.session.commit()
            print(f"✅ Tabelas criadas para escritório: {office}")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
