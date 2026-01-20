from sqlalchemy import text
from models.models import db, Office
import re

def sanitize_office_name(name):
    """
    Sanitiza o nome do escritório para criar um código válido
    
    Regras:
    - Remove acentos
    - Converte para minúsculas
    - Substitui espaços por underscores
    - Remove caracteres especiais
    - Mantém apenas letras, números e underscores
    
    Exemplos:
        "São Paulo" -> "sao_paulo"
        "Escritório Central" -> "escritorio_central"
        "Norte 01" -> "norte_01"
    """
    
    # Remover acentos
    replacements = {
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n'
    }
    
    name = name.lower()
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Substituir espaços por underscores
    name = name.replace(' ', '_')
    
    # Remover caracteres especiais (manter apenas letras, números e underscores)
    name = re.sub(r'[^a-z0-9_]', '', name)
    
    # Remover underscores múltiplos
    name = re.sub(r'_+', '_', name)
    
    # Remover underscores no início e fim
    name = name.strip('_')
    
    return name

def list_offices():
    """
    Lista todos os escritórios existentes (tabelas office_*)
    
    Returns:
        Lista de códigos de escritórios (sem o prefixo office_)
    """
    
    query = text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'office_%' AND name NOT LIKE '%_deleted'
        ORDER BY name
    """)
    
    result = db.session.execute(query)
    tables = [row[0] for row in result]
    
    # Remover prefixo 'office_'
    offices = [table.replace('office_', '') for table in tables]
    
    return offices

def ensure_office_exists(office_code):
    """
    Garante que as tabelas do escritório existam
    
    Args:
        office_code: Código do escritório (já sanitizado)
    
    Returns:
        True se criou as tabelas, False se já existiam
    """
    
    table_name = f'office_{office_code}'
    deleted_table = f'{table_name}_deleted'
    
    # Verificar se a tabela já existe
    check_query = text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = db.session.execute(check_query).fetchone()
    
    if result:
        return False  # Já existe
    
    # Criar tabela principal
    create_table_query = text(f"""
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL,
            tipo_acao TEXT,
            data_fechamento DATE,
            pendencias TEXT,
            numero_processo TEXT,
            data_protocolo DATE,
            observacoes TEXT,
            captador_pago TEXT,
            nome_captador TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER
        )
    """)
    db.session.execute(create_table_query)
    
    # Criar tabela de excluídos
    create_deleted_query = text(f"""
        CREATE TABLE {deleted_table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_id INTEGER,
            nome TEXT,
            cpf TEXT,
            tipo_acao TEXT,
            data_fechamento DATE,
            pendencias TEXT,
            numero_processo TEXT,
            data_protocolo DATE,
            observacoes TEXT,
            captador_pago TEXT,
            nome_captador TEXT,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_by INTEGER,
            original_created_at TIMESTAMP,
            original_updated_at TIMESTAMP
        )
    """)
    db.session.execute(create_deleted_query)
    
    db.session.commit()
    
    print(f"✅ Tabelas criadas para escritório: {office_code}")
    
    return True

def get_office_name(office_code):
    """
    Retorna o nome de exibição do escritório
    
    Args:
        office_code: Código do escritório
    
    Returns:
        Nome de exibição ou código em maiúsculas se não encontrado
    """
    
    office = Office.query.filter_by(code=office_code).first()
    
    if office:
        return office.name
    
    # Se não encontrar no banco, retornar código formatado
    return office_code.upper().replace('_', ' ')

def office_exists(office_code):
    """Verifica se um escritório existe"""
    
    table_name = f'office_{office_code}'
    
    check_query = text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = db.session.execute(check_query).fetchone()
    
    return result is not None

def get_office_record_count(office_code):
    """Retorna o número de registros em um escritório"""
    
    if not office_exists(office_code):
        return 0
    
    table_name = f'office_{office_code}'
    
    count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
    result = db.session.execute(count_query).fetchone()
    
    return result[0] if result else 0
