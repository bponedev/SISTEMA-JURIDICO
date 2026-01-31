from models.models import db, AuditLog
from flask_login import current_user
from flask import request
import json

def log_action(action, table_name, record_id=None, details=None):
    """
    Registra uma ação no log de auditoria
    
    Args:
        action: Tipo de ação (CREATE, UPDATE, DELETE, RESTORE, MIGRATE, LOGIN, LOGOUT)
        table_name: Nome da tabela afetada
        record_id: ID do registro afetado (opcional)
        details: Detalhes adicionais da operação (string ou dict)
    """
    
    try:
        # Converter details para string se for dict
        if isinstance(details, dict):
            details = json.dumps(details, ensure_ascii=False)
        
        # Obter IP do usuário
        ip_address = request.remote_addr if request else None
        
        # Obter ID do usuário
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        
        # Criar log
        log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            details=details,
            ip_address=ip_address
        )
        
        db.session.add(log)
        db.session.commit()
        
        return True
    
    except Exception as e:
        print(f"Erro ao criar log de auditoria: {e}")
        db.session.rollback()
        return False

def get_recent_logs(limit=100):
    """Retorna os logs mais recentes"""
    return AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

def get_user_logs(user_id, limit=50):
    """Retorna logs de um usuário específico"""
    return AuditLog.query.filter_by(user_id=user_id).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()

def get_table_logs(table_name, record_id=None, limit=50):
    """Retorna logs de uma tabela específica"""
    query = AuditLog.query.filter_by(table_name=table_name)
    
    if record_id:
        query = query.filter_by(record_id=record_id)
    
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
