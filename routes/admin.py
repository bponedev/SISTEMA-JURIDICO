from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.models import db, User, AuditLog
from utils.permissions import require_role
from utils.audit import log_action
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'ADMIN':
            flash('Acesso restrito a administradores.', 'error')
            return redirect(url_for('clients.list_clients'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    """Lista todos os usuários"""
    users = User.query.order_by(User.id).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Criar novo usuário"""
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        nome = request.form.get('nome', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'VISUALIZADOR')
        offices = request.form.getlist('offices')
        ativo = request.form.get('ativo') == 'on'
        
        # Validações
        if not username or not nome or not password:
            flash('Username, nome e senha são obrigatórios.', 'error')
            return render_template('admin/user_create.html')
        
        if role not in ['ADMIN', 'SUPERVISOR', 'OPERADOR', 'VISUALIZADOR']:
            flash('Papel inválido.', 'error')
            return render_template('admin/user_create.html')
        
        # Verificar se username já existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username já existe.', 'error')
            return render_template('admin/user_create.html')
        
        # Criar usuário
        new_user = User(
            username=username,
            nome=nome,
            role=role,
            ativo=ativo
        )
        new_user.set_password(password)
        new_user.set_offices_list(offices)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            log_action('CREATE', 'users', new_user.id, f'Usuário criado: {username}')
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
    
    from utils.offices import list_offices
    return render_template('admin/user_create.html', offices=list_offices())

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Editar usuário"""
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        role = request.form.get('role', 'VISUALIZADOR')
        offices = request.form.getlist('offices')
        ativo = request.form.get('ativo') == 'on'
        
        if not nome:
            flash('Nome é obrigatório.', 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        if role not in ['ADMIN', 'SUPERVISOR', 'OPERADOR', 'VISUALIZADOR']:
            flash('Papel inválido.', 'error')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        user.nome = nome
        user.role = role
        user.ativo = ativo
        user.set_offices_list(offices)
        
        try:
            db.session.commit()
            log_action('UPDATE', 'users', user_id, f'Usuário atualizado: {user.username}')
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    
    from utils.offices import list_offices
    return render_template('admin/user_edit.html', user=user, offices=list_offices())

@admin_bp.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    """Redefinir senha do usuário"""
    
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '').strip()
    
    if not new_password:
        return jsonify({'success': False, 'message': 'Senha não pode ser vazia'}), 400
    
    try:
        user.set_password(new_password)
        db.session.commit()
        
        log_action('UPDATE', 'users', user_id, f'Senha redefinida para: {user.username}')
        return jsonify({'success': True, 'message': 'Senha redefinida com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Ativar/Desativar usuário"""
    
    user = User.query.get_or_404(user_id)
    
    # Não permitir desativar o próprio usuário
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Você não pode desativar sua própria conta'}), 400
    
    try:
        user.ativo = not user.ativo
        db.session.commit()
        
        status = 'ativado' if user.ativo else 'desativado'
        log_action('UPDATE', 'users', user_id, f'Usuário {status}: {user.username}')
        
        return jsonify({'success': True, 'message': f'Usuário {status} com sucesso', 'ativo': user.ativo})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Excluir usuário"""
    
    user = User.query.get_or_404(user_id)
    
    # Não permitir excluir o próprio usuário
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Você não pode excluir sua própria conta'}), 400
    
    # Não permitir excluir o admin padrão
    if user.username == 'admin':
        return jsonify({'success': False, 'message': 'Não é possível excluir o admin padrão'}), 400
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        log_action('DELETE', 'users', user_id, f'Usuário excluído: {username}')
        return jsonify({'success': True, 'message': 'Usuário excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/audit')
@login_required
@admin_required
def audit_log():
    """Visualizar log de auditoria"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/audit.html', logs=logs)
