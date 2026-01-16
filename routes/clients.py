from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
from app import db
from models.models import Client

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')


@clients_bp.route('/', methods=['GET', 'POST'])
@login_required
def form():
    if request.method == 'POST':
        client = Client(
            nome=request.form['nome'],
            cpf=request.form['cpf'],
            escritorio=request.form['escritorio'],
            tipo_acao=request.form.get('tipo_acao'),
            data_contrato=request.form.get('data_contrato'),
            data_protocolo=request.form.get('data_protocolo'),
            numero_processo=request.form.get('numero_processo'),
            pendencias=request.form.get('pendencias'),
            observacoes=request.form.get('observacoes'),
            captador=request.form.get('captador'),
            captador_pago=request.form.get('captador_pago')
        )
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('clients.form'))

    clients = Client.query.filter_by(excluido=False).all()
    return render_template('clients.html', clients=clients)
