from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def require_permission(action, office=None):
    """
    Decorator para verificar permissões
    
    Args:
        action: Ação requerida (view, create, edit, delete, migrate)
        office: Escritório específico (opcional, será verificado na rota)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor, faça login.', 'error')
                return redirect(url_for('auth.login'))
            
            # Se office não foi passado, tentar obter dos kwargs da rota
            check_office = office
            if not check_office and 'office' in kwargs:
                check_office = kwargs['office']
            
            # Verificar permissão
            if not current_user.has_permission(action, check_office):
                flash('Você não tem permissão para executar esta ação.', 'error')
                return redirect(url_for('clients.list_clients'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(*roles):
    """
    Decorator para verificar papel do usuário
    
    Args:
        *roles: Lista de papéis permitidos (ADMIN, SUPERVISOR, OPERADOR, VISUALIZADOR)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor, faça login.', 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('Você não tem permissão para acessar esta página.', 'error')
                return redirect(url_for('clients.list_clients'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def can_edit_office(office):
    """Verifica se o usuário pode editar um escritório específico"""
    if not current_user.is_authenticated:
        return False
    
    return current_user.has_permission('edit', office)

def can_view_office(office):
    """Verifica se o usuário pode visualizar um escritório específico"""
    if not current_user.is_authenticated:
        return False
    
    return current_user.has_permission('view', office)

def get_user_editable_offices():
    """Retorna lista de escritórios que o usuário pode editar"""
    if not current_user.is_authenticated:
        return []
    
    if current_user.role in ['ADMIN', 'SUPERVISOR']:
        from utils.offices import list_offices
        return list_offices()
    
    if current_user.role == 'OPERADOR':
        return current_user.get_offices_list()
    
    return []

def get_user_viewable_offices():
    """Retorna lista de escritórios que o usuário pode visualizar"""
    if not current_user.is_authenticated:
        return []
    
    # Todos podem visualizar todos os escritórios
    from utils.offices import list_offices
    return list_offices()
