from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy import text
from models.models import db
from utils.permissions import require_permission
from utils.audit import log_action
from utils.offices import list_offices, sanitize_office_name
import io
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/')
@login_required
def list_clients():
    """Lista clientes com paginação, busca e filtros"""
    
    # Parâmetros
    office = request.args.get('office', 'todos')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Validar per_page
    if per_page not in [10, 20, 50, 100]:
        per_page = 20
    
    # Busca
    filtro = request.args.get('filtro', '')  # nome, cpf, id
    valor = request.args.get('valor', '').strip()
    
    # Filtro por data
    data_tipo = request.args.get('data_tipo', '')  # data_fechamento, data_protocolo
    data_de = request.args.get('data_de', '')
    data_ate = request.args.get('data_ate', '')
    
    # Listar escritórios disponíveis
    all_offices = list_offices()
    
    # Filtrar escritórios que o usuário pode visualizar
    if current_user.role == 'OPERADOR':
        user_offices = current_user.get_offices_list()
        # OPERADOR pode visualizar todos, mas só editar os seus
        viewable_offices = all_offices
    else:
        viewable_offices = all_offices
    
    # Determinar quais escritórios buscar
    if office == 'todos':
        offices_to_search = viewable_offices
    else:
        if office in viewable_offices:
            offices_to_search = [office]
        else:
            flash('Você não tem permissão para visualizar este escritório.', 'error')
            return redirect(url_for('clients.list_clients'))
    
    # Buscar registros
    all_records = []
    
    for off in offices_to_search:
        table_name = f'office_{off}'
        
        # Construir query
        query = f"SELECT *, '{off}' as office FROM {table_name} WHERE 1=1"
        params = {}
        
        # Aplicar filtro de busca
        if filtro and valor:
            if filtro == 'nome':
                query += " AND nome LIKE :valor"
                params['valor'] = f'%{valor}%'
            elif filtro == 'cpf':
                query += " AND cpf LIKE :valor"
                params['valor'] = f'%{valor}%'
            elif filtro == 'id':
                try:
                    query += " AND id = :valor"
                    params['valor'] = int(valor)
                except ValueError:
                    continue
        
        # Aplicar filtro de data
        if data_tipo and data_de:
            query += f" AND {data_tipo} >= :data_de"
            params['data_de'] = data_de
        
        if data_tipo and data_ate:
            query += f" AND {data_tipo} <= :data_ate"
            params['data_ate'] = data_ate
        
        query += " ORDER BY id DESC"
        
        try:
            result = db.session.execute(text(query), params)
            records = [dict(row._mapping) for row in result]
            all_records.extend(records)
        except Exception as e:
            print(f"Erro ao buscar em {table_name}: {e}")
    
    # Paginação manual
    total = len(all_records)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_records = all_records[start:end]
    
    return render_template('clients/list.html',
                         records=paginated_records,
                         offices=viewable_offices,
                         current_office=office,
                         page=page,
                         per_page=per_page,
                         total=total,
                         total_pages=total_pages,
                         filtro=filtro,
                         valor=valor,
                         data_tipo=data_tipo,
                         data_de=data_de,
                         data_ate=data_ate)

@clients_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('create')
def create_client():
    """Criar novo cliente"""
    
    if request.method == 'POST':
        # Dados do formulário
        office = request.form.get('office', '').strip().lower()
        nome = request.form.get('nome', '').strip()
        cpf = request.form.get('cpf', '').strip()
        tipo_acao = request.form.get('tipo_acao', '').strip()
        data_fechamento = request.form.get('data_fechamento', '').strip()
        pendencias = request.form.get('pendencias', '').strip()
        numero_processo = request.form.get('numero_processo', '').strip()
        data_protocolo = request.form.get('data_protocolo', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        captador_pago = request.form.get('captador_pago', '').strip()
        nome_captador = request.form.get('nome_captador', '').strip()
        
        # Validações
        if not office or not nome or not cpf:
            flash('Escritório, Nome e CPF são obrigatórios.', 'error')
            return render_template('clients/create.html', offices=list_offices())
        
        # Sanitizar nome do escritório
        office = sanitize_office_name(office)
        
        # Verificar permissão para este escritório
        if not current_user.has_permission('create', office):
            flash('Você não tem permissão para criar clientes neste escritório.', 'error')
            return redirect(url_for('clients.list_clients'))
        
        # Verificar se escritório existe, senão criar
        from utils.offices import ensure_office_exists
        ensure_office_exists(office)
        
        table_name = f'office_{office}'
        
        # Inserir registro
        query = text(f"""
            INSERT INTO {table_name} 
            (nome, cpf, tipo_acao, data_fechamento, pendencias, numero_processo, 
             data_protocolo, observacoes, captador_pago, nome_captador, created_by, updated_by)
            VALUES 
            (:nome, :cpf, :tipo_acao, :data_fechamento, :pendencias, :numero_processo,
             :data_protocolo, :observacoes, :captador_pago, :nome_captador, :created_by, :updated_by)
        """)
        
        try:
            db.session.execute(query, {
                'nome': nome,
                'cpf': cpf,
                'tipo_acao': tipo_acao or None,
                'data_fechamento': data_fechamento or None,
                'pendencias': pendencias or None,
                'numero_processo': numero_processo or None,
                'data_protocolo': data_protocolo or None,
                'observacoes': observacoes or None,
                'captador_pago': captador_pago or None,
                'nome_captador': nome_captador or None,
                'created_by': current_user.id,
                'updated_by': current_user.id
            })
            db.session.commit()
            
            log_action('CREATE', table_name, None, f'Cliente criado: {nome} (CPF: {cpf})')
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('clients.list_clients', office=office))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar cliente: {str(e)}', 'error')
            return render_template('clients/create.html', offices=list_offices())
    
    return render_template('clients/create.html', offices=list_offices())
