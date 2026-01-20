from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # ADMIN, SUPERVISOR, OPERADOR, VISUALIZADOR
    offices = db.Column(db.Text)  # Lista de escritórios separados por vírgula
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_offices_list(self):
        """Retorna lista de escritórios do usuário"""
        if not self.offices:
            return []
        return [o.strip() for o in self.offices.split(',') if o.strip()]
    
    def set_offices_list(self, offices_list):
        """Define lista de escritórios do usuário"""
        if offices_list:
            self.offices = ','.join(offices_list)
        else:
            self.offices = ''
    
    def has_permission(self, action, office=None):
        """
        Verifica se o usuário tem permissão para executar uma ação
        
        Regras:
        - ADMIN: acesso total a tudo
        - SUPERVISOR: pode editar todos os escritórios
        - OPERADOR: pode editar apenas escritórios atribuídos, visualizar todos
        - VISUALIZADOR: apenas visualizar todos
        """
        if not self.ativo:
            return False
        
        if self.role == 'ADMIN':
            return True
        
        if self.role == 'SUPERVISOR':
            if action in ['view', 'edit', 'create', 'delete', 'migrate']:
                return True
        
        if self.role == 'OPERADOR':
            if action == 'view':
                return True
            if action in ['edit', 'create', 'delete', 'migrate']:
                if office:
                    return office in self.get_offices_list()
                return False
        
        if self.role == 'VISUALIZADOR':
            if action == 'view':
                return True
            return False
        
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'


class Office(db.Model):
    __tablename__ = 'offices'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # Ex: central, campos, norte
    name = db.Column(db.String(200), nullable=False)  # Nome para exibição
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Office {self.code}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, RESTORE, MIGRATE
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON com detalhes da operação
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'
