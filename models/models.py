from flask_login import UserMixin
from app import db, login_manager

from database import db

class Office(db.Model):
    __tablename__ = 'offices'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True)

    clients = db.relationship('Client', backref='office', lazy=True)

    def __repr__(self):
        return f'<Office {self.code} - {self.name}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(20), nullable=False)

    escritorio = db.Column(db.String(120), nullable=False)
    tipo_acao = db.Column(db.String(120))

    data_contrato = db.Column(db.String(10))
    data_protocolo = db.Column(db.String(10))

    numero_processo = db.Column(db.String(120))
    pendencias = db.Column(db.Text)
    observacoes = db.Column(db.Text)

    captador = db.Column(db.String(120))
    captador_pago = db.Column(db.String(20))

    excluido = db.Column(db.Boolean, default=False)
