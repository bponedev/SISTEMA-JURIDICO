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

@clients_bp.route('/edit/<office>/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(office, client_id):
    """Editar cliente"""
    
    # Verificar permissão
    if not current_user.has_permission('edit', office):
        flash('Você não tem permissão para editar clientes neste escritório.', 'error')
        return redirect(url_for('clients.list_clients'))
    
    table_name = f'office_{office}'
    
    if request.method == 'POST':
        # Dados do formulário
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
        
        if not nome or not cpf:
            flash('Nome e CPF são obrigatórios.', 'error')
            return redirect(url_for('clients.edit_client', office=office, client_id=client_id))
        
        query = text(f"""
            UPDATE {table_name}
            SET nome = :nome, cpf = :cpf, tipo_acao = :tipo_acao,
                data_fechamento = :data_fechamento, pendencias = :pendencias,
                numero_processo = :numero_processo, data_protocolo = :data_protocolo,
                observacoes = :observacoes, captador_pago = :captador_pago,
                nome_captador = :nome_captador, updated_by = :updated_by,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
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
                'updated_by': current_user.id,
                'id': client_id
            })
            db.session.commit()
            
            log_action('UPDATE', table_name, client_id, f'Cliente atualizado: {nome}')
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('clients.list_clients', office=office))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar cliente: {str(e)}', 'error')
    
    # Buscar cliente
    query = text(f"SELECT * FROM {table_name} WHERE id = :id")
    result = db.session.execute(query, {'id': client_id}).fetchone()
    
    if not result:
        flash('Cliente não encontrado.', 'error')
        return redirect(url_for('clients.list_clients'))
    
    client = dict(result._mapping)
    
    return render_template('clients/edit.html', client=client, office=office)

@clients_bp.route('/delete', methods=['POST'])
@login_required
def delete_clients():
    """Excluir cliente(s) - soft delete"""
    
    office = request.form.get('office')
    client_ids = request.form.getlist('client_ids[]')
    
    if not office or not client_ids:
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
    
    # Verificar permissão
    if not current_user.has_permission('delete', office):
        return jsonify({'success': False, 'message': 'Sem permissão'}), 403
    
    table_name = f'office_{office}'
    deleted_table = f'{table_name}_deleted'
    
    try:
        for client_id in client_ids:
            # Buscar registro original
            query = text(f"SELECT * FROM {table_name} WHERE id = :id")
            result = db.session.execute(query, {'id': client_id}).fetchone()
            
            if result:
                record = dict(result._mapping)
                
                # Inserir na tabela de excluídos
                insert_query = text(f"""
                    INSERT INTO {deleted_table}
                    (original_id, nome, cpf, tipo_acao, data_fechamento, pendencias,
                     numero_processo, data_protocolo, observacoes, captador_pago,
                     nome_captador, deleted_by, original_created_at, original_updated_at)
                    VALUES
                    (:original_id, :nome, :cpf, :tipo_acao, :data_fechamento, :pendencias,
                     :numero_processo, :data_protocolo, :observacoes, :captador_pago,
                     :nome_captador, :deleted_by, :original_created_at, :original_updated_at)
                """)
                
                db.session.execute(insert_query, {
                    'original_id': record['id'],
                    'nome': record['nome'],
                    'cpf': record['cpf'],
                    'tipo_acao': record.get('tipo_acao'),
                    'data_fechamento': record.get('data_fechamento'),
                    'pendencias': record.get('pendencias'),
                    'numero_processo': record.get('numero_processo'),
                    'data_protocolo': record.get('data_protocolo'),
                    'observacoes': record.get('observacoes'),
                    'captador_pago': record.get('captador_pago'),
                    'nome_captador': record.get('nome_captador'),
                    'deleted_by': current_user.id,
                    'original_created_at': record.get('created_at'),
                    'original_updated_at': record.get('updated_at')
                })
                
                # Excluir da tabela principal
                delete_query = text(f"DELETE FROM {table_name} WHERE id = :id")
                db.session.execute(delete_query, {'id': client_id})
                
                log_action('DELETE', table_name, client_id, f'Cliente excluído: {record["nome"]}')
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cliente(s) excluído(s) com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@clients_bp.route('/deleted/<office>')
@login_required
def list_deleted(office):
    """Listar clientes excluídos"""
    
    if office not in list_offices():
        flash('Escritório não encontrado.', 'error')
        return redirect(url_for('clients.list_clients'))
    
    deleted_table = f'office_{office}_deleted'
    
    query = text(f"SELECT * FROM {deleted_table} ORDER BY deleted_at DESC")
    result = db.session.execute(query)
    deleted_records = [dict(row._mapping) for row in result]
    
    return render_template('clients/deleted.html', 
                         records=deleted_records, 
                         office=office)

@clients_bp.route('/restore', methods=['POST'])
@login_required
def restore_clients():
    """Restaurar cliente(s) excluído(s)"""
    
    office = request.form.get('office')
    deleted_ids = request.form.getlist('deleted_ids[]')
    
    if not office or not deleted_ids:
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
    
    # Verificar permissão
    if not current_user.has_permission('create', office):
        return jsonify({'success': False, 'message': 'Sem permissão'}), 403
    
    table_name = f'office_{office}'
    deleted_table = f'{table_name}_deleted'
    
    try:
        for deleted_id in deleted_ids:
            # Buscar registro excluído
            query = text(f"SELECT * FROM {deleted_table} WHERE id = :id")
            result = db.session.execute(query, {'id': deleted_id}).fetchone()
            
            if result:
                record = dict(result._mapping)
                
                # Restaurar na tabela principal
                insert_query = text(f"""
                    INSERT INTO {table_name}
                    (nome, cpf, tipo_acao, data_fechamento, pendencias, numero_processo,
                     data_protocolo, observacoes, captador_pago, nome_captador,
                     created_by, updated_by, created_at, updated_at)
                    VALUES
                    (:nome, :cpf, :tipo_acao, :data_fechamento, :pendencias, :numero_processo,
                     :data_protocolo, :observacoes, :captador_pago, :nome_captador,
                     :created_by, :updated_by, :created_at, :updated_at)
                """)
                
                db.session.execute(insert_query, {
                    'nome': record['nome'],
                    'cpf': record['cpf'],
                    'tipo_acao': record.get('tipo_acao'),
                    'data_fechamento': record.get('data_fechamento'),
                    'pendencias': record.get('pendencias'),
                    'numero_processo': record.get('numero_processo'),
                    'data_protocolo': record.get('data_protocolo'),
                    'observacoes': record.get('observacoes'),
                    'captador_pago': record.get('captador_pago'),
                    'nome_captador': record.get('nome_captador'),
                    'created_by': current_user.id,
                    'updated_by': current_user.id,
                    'created_at': record.get('original_created_at'),
                    'updated_at': datetime.utcnow()
                })
                
                # Remover da tabela de excluídos
                delete_query = text(f"DELETE FROM {deleted_table} WHERE id = :id")
                db.session.execute(delete_query, {'id': deleted_id})
                
                log_action('RESTORE', table_name, None, f'Cliente restaurado: {record["nome"]}')
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Cliente(s) restaurado(s) com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@clients_bp.route('/migrate', methods=['POST'])
@login_required
def migrate_client():
    """Migrar cliente único para outro escritório"""
    
    client_id = request.form.get('id')
    office_current = request.form.get('office_current')
    office_target = request.form.get('office_target')
    
    if not all([client_id, office_current, office_target]):
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
    
    if office_current == office_target:
        return jsonify({'success': False, 'message': 'Escritórios devem ser diferentes'}), 400
    
    # Verificar permissões
    if not current_user.has_permission('migrate', office_current):
        return jsonify({'success': False, 'message': 'Sem permissão no escritório origem'}), 403
    
    if not current_user.has_permission('migrate', office_target):
        return jsonify({'success': False, 'message': 'Sem permissão no escritório destino'}), 403
    
    table_current = f'office_{office_current}'
    table_target = f'office_{office_target}'
    
    try:
        # Buscar registro
        query = text(f"SELECT * FROM {table_current} WHERE id = :id")
        result = db.session.execute(query, {'id': client_id}).fetchone()
        
        if not result:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        record = dict(result._mapping)
        
        # Inserir no escritório destino
        insert_query = text(f"""
            INSERT INTO {table_target}
            (nome, cpf, tipo_acao, data_fechamento, pendencias, numero_processo,
             data_protocolo, observacoes, captador_pago, nome_captador,
             created_by, updated_by, created_at)
            VALUES
            (:nome, :cpf, :tipo_acao, :data_fechamento, :pendencias, :numero_processo,
             :data_protocolo, :observacoes, :captador_pago, :nome_captador,
             :created_by, :updated_by, :created_at)
        """)
        
        db.session.execute(insert_query, {
            'nome': record['nome'],
            'cpf': record['cpf'],
            'tipo_acao': record.get('tipo_acao'),
            'data_fechamento': record.get('data_fechamento'),
            'pendencias': record.get('pendencias'),
            'numero_processo': record.get('numero_processo'),
            'data_protocolo': record.get('data_protocolo'),
            'observacoes': record.get('observacoes'),
            'captador_pago': record.get('captador_pago'),
            'nome_captador': record.get('nome_captador'),
            'created_by': record.get('created_by', current_user.id),
            'updated_by': current_user.id,
            'created_at': record.get('created_at')
        })
        
        # Excluir do escritório origem
        delete_query = text(f"DELETE FROM {table_current} WHERE id = :id")
        db.session.execute(delete_query, {'id': client_id})
        
        db.session.commit()
        
        log_action('MIGRATE', table_current, client_id, 
                  f'Cliente migrado de {office_current} para {office_target}: {record["nome"]}')
        
        return jsonify({'success': True, 'message': 'Cliente migrado com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@clients_bp.route('/migrate_selected', methods=['POST'])
@login_required
def migrate_selected():
    """Migrar múltiplos clientes para outro escritório"""
    
    client_ids = request.form.getlist('ids[]')
    office_current = request.form.get('office_current')
    office_target = request.form.get('office_target')
    
    if not all([client_ids, office_current, office_target]):
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
    
    if office_current == office_target:
        return jsonify({'success': False, 'message': 'Escritórios devem ser diferentes'}), 400
    
    # Verificar permissões
    if not current_user.has_permission('migrate', office_current):
        return jsonify({'success': False, 'message': 'Sem permissão no escritório origem'}), 403
    
    if not current_user.has_permission('migrate', office_target):
        return jsonify({'success': False, 'message': 'Sem permissão no escritório destino'}), 403
    
    table_current = f'office_{office_current}'
    table_target = f'office_{office_target}'
    
    try:
        migrated_count = 0
        
        for client_id in client_ids:
            # Buscar registro
            query = text(f"SELECT * FROM {table_current} WHERE id = :id")
            result = db.session.execute(query, {'id': client_id}).fetchone()
            
            if result:
                record = dict(result._mapping)
                
                # Inserir no escritório destino
                insert_query = text(f"""
                    INSERT INTO {table_target}
                    (nome, cpf, tipo_acao, data_fechamento, pendencias, numero_processo,
                     data_protocolo, observacoes, captador_pago, nome_captador,
                     created_by, updated_by, created_at)
                    VALUES
                    (:nome, :cpf, :tipo_acao, :data_fechamento, :pendencias, :numero_processo,
                     :data_protocolo, :observacoes, :captador_pago, :nome_captador,
                     :created_by, :updated_by, :created_at)
                """)
                
                db.session.execute(insert_query, {
                    'nome': record['nome'],
                    'cpf': record['cpf'],
                    'tipo_acao': record.get('tipo_acao'),
                    'data_fechamento': record.get('data_fechamento'),
                    'pendencias': record.get('pendencias'),
                    'numero_processo': record.get('numero_processo'),
                    'data_protocolo': record.get('data_protocolo'),
                    'observacoes': record.get('observacoes'),
                    'captador_pago': record.get('captador_pago'),
                    'nome_captador': record.get('nome_captador'),
                    'created_by': record.get('created_by', current_user.id),
                    'updated_by': current_user.id,
                    'created_at': record.get('created_at')
                })
                
                # Excluir do escritório origem
                delete_query = text(f"DELETE FROM {table_current} WHERE id = :id")
                db.session.execute(delete_query, {'id': client_id})
                
                log_action('MIGRATE', table_current, client_id,
                          f'Cliente migrado (lote) de {office_current} para {office_target}: {record["nome"]}')
                
                migrated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{migrated_count} cliente(s) migrado(s) com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@clients_bp.route('/export/csv')
@login_required
def export_csv():
    """Exportar dados para CSV"""
    
    office = request.args.get('office', 'todos')
    
    # Determinar escritórios
    if office == 'todos':
        offices_to_export = list_offices()
    else:
        offices_to_export = [office]
    
    # Coletar dados
    all_records = []
    
    for off in offices_to_export:
        table_name = f'office_{off}'
        query = text(f"SELECT *, '{off}' as escritorio FROM {table_name} ORDER BY id")
        result = db.session.execute(query)
        records = [dict(row._mapping) for row in result]
        all_records.extend(records)
    
    # Criar CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'id', 'escritorio', 'nome', 'cpf', 'tipo_acao', 'data_fechamento',
        'pendencias', 'numero_processo', 'data_protocolo', 'observacoes',
        'captador_pago', 'nome_captador', 'created_at', 'updated_at'
    ])
    
    writer.writeheader()
    writer.writerows(all_records)
    
    # Preparar download
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'clientes_{office}_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@clients_bp.route('/export/pdf')
@login_required
def export_pdf():
    """Exportar dados para PDF"""
    
    office = request.args.get('office', 'todos')
    
    # Determinar escritórios
    if office == 'todos':
        offices_to_export = list_offices()
    else:
        offices_to_export = [office]
    
    # Coletar dados
    all_records = []
    
    for off in offices_to_export:
        table_name = f'office_{off}'
        query = text(f"SELECT *, '{off}' as escritorio FROM {table_name} ORDER BY id")
        result = db.session.execute(query)
        records = [dict(row._mapping) for row in result]
        all_records.extend(records)
    
    # Criar PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    
    # Preparar dados da tabela
    data = [['ID', 'Escritório', 'Nome', 'CPF', 'Tipo Ação', 'Data Fechamento']]
    
    for record in all_records:
        data.append([
            str(record.get('id', '')),
            record.get('escritorio', ''),
            record.get('nome', ''),
            record.get('cpf', ''),
            record.get('tipo_acao', ''),
            record.get('data_fechamento', '')
        ])
    
    # Criar tabela
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'clientes_{office}_{datetime.now().strftime("%Y%m%d")}.pdf'
    )
