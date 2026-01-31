from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.models import db, User
from utils.audit import log_action

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('clients.list_clients'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Usuário e senha são obrigatórios.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.ativo:
                flash('Usuário inativo. Contate o administrador.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=True)
            log_action('LOGIN', 'users', user.id, f'Login realizado: {username}')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('clients.list_clients'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_action('LOGOUT', 'users', current_user.id, f'Logout realizado: {current_user.username}')
    logout_user()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('auth.login'))
