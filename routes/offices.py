from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text
from models.models import db, Office
from utils.offices import list_offices, sanitize_office_name, ensure_office_exists
from utils.audit import log_action

offices_bp = Blueprint('offices', __name__, url_prefix='/offices')

def admin_or_supervisor_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['ADMIN', 'SUPERVISOR']:
            flash('Acesso restrito.', 'error')
            return redirect(url_for('clients.list_clients'))
        return f(*args, **kwargs)
    return decorated_function

@offices_bp.route('/')
@login_required
@admin_or_supervisor_required
def manage_offices():
    """Gerenciar escritórios"""
    
    # Listar escritórios existentes
    offices = Office.query.filter_by(ativo=True).order_by(Office.name).all()
    
    # Listar tabelas dinâmicas
    dynamic_offices = list_offices()
    
    return render_template('offices/manage.html', 
                         offices=offices,
                         dynamic_offices=dynamic_offices)

@offices_bp.route('/create', methods=['POST'])
@login_required
@admin_or_supervisor_required
def create_office():
    """Criar novo escritório"""
    
    name = request.form.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': 'Nome do escritório é obrigatório'}), 400
    
    # Sanitizar nome para criar código
    code = sanitize_office_name(name)
    
    # Verificar se já existe
    existing = Office.query.filter_by(code=code).first()
    if existing:
        return jsonify({'success': False, 'message': 'Escritório já existe'}), 400
    
    try:
        # Criar registro do escritório
        office = Office(
            code=code,
            name=name,
            ativo=True,
            created_by=current_user.id
        )
        db.session.add(office)
        
        # Criar tabelas do escritório
        ensure_office_exists(code)
        
        db.session.commit()
        
        log_action('CREATE', 'offices', office.id, f'Escritório criado: {name} ({code})')
        
        return jsonify({
            'success': True, 
            'message': 'Escritório criado com sucesso',
            'office': {'code': code, 'name': name}
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@offices_bp.route('/edit/<int:office_id>', methods=['POST'])
@login_required
@admin_or_supervisor_required
def edit_office(office_id):
    """Editar nome do escritório"""
    
    office = Office.query.get_or_404(office_id)
    new_name = request.form.get('name', '').strip()
    
    if not new_name:
        return jsonify({'success': False, 'message': 'Nome não pode ser vazio'}), 400
    
    try:
        old_name = office.name
        office.name = new_name
        db.session.commit()
        
        log_action('UPDATE', 'offices', office_id, f'Escritório renomeado: {old_name} → {new_name}')
        
        return jsonify({'success': True, 'message': 'Nome atualizado com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@offices_bp.route('/delete/<int:office_id>', methods=['POST'])
@login_required
@admin_or_supervisor_required
def delete_office(office_id):
    """Excluir escritório (soft delete)"""
    
    office = Office.query.get_or_404(office_id)
    
    # Verificar se há registros no escritório
    table_name = f'office_{office.code}'
    
    try:
        count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
        result = db.session.execute(count_query).fetchone()
        count = result[0] if result else 0
        
        if count > 0:
            return jsonify({
                'success': False, 
                'message': f'Não é possível excluir. Existem {count} cliente(s) neste escritório.'
            }), 400
        
        # Desativar escritório (soft delete)
        office.ativo = False
        db.session.commit()
        
        log_action('DELETE', 'offices', office_id, f'Escritório desativado: {office.name}')
        
        return jsonify({'success': True, 'message': 'Escritório excluído com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@offices_bp.route('/stats')
@login_required
def office_stats():
    """Estatísticas dos escritórios"""
    
    offices = list_offices()
    stats = []
    
    for office in offices:
        table_name = f'office_{office}'
        
        try:
            # Contar registros ativos
            count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
            result = db.session.execute(count_query).fetchone()
            active_count = result[0] if result else 0
            
            # Contar registros excluídos
            deleted_table = f'{table_name}_deleted'
            deleted_query = text(f"SELECT COUNT(*) as count FROM {deleted_table}")
            result = db.session.execute(deleted_query).fetchone()
            deleted_count = result[0] if result else 0
            
            # Buscar nome do escritório
            office_obj = Office.query.filter_by(code=office).first()
            office_name = office_obj.name if office_obj else office.upper()
            
            stats.append({
                'code': office,
                'name': office_name,
                'active': active_count,
                'deleted': deleted_count,
                'total': active_count + deleted_count
            })
        
        except Exception as e:
            print(f"Erro ao buscar stats de {office}: {e}")
    
    return render_template('offices/stats.html', stats=stats)
