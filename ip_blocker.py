import time
import re
import secrets
from collections import defaultdict
from flask import request, jsonify, render_template, make_response

# Estruturas de dados
failed_attempts = defaultdict(list)  # user_id → lista de timestamps
blocked_users = {}  # user_id → timestamp de desbloqueio
blocked_reasons = {}  # user_id → motivo

# Configurações
BLOCK_TIME = 900  # 15 minutos
ATTACK_BLOCK_TIME = 3600  # 1 hora

# Padrões de ATAQUE
ATTACK_PATTERNS = [
    r'<script', r'javascript:', r'onerror=', r'alert\(', r'<iframe',
    r' UNION ', r' SELECT ', r' DROP ', r' DELETE ', r' INSERT ',
    r" OR '1'='1", r' OR 1=1', r'--', r';.*DROP', r'<img.*onerror'
]

def get_user_id():
    """Obtém um identificador único para o utilizador (baseado em cookie)."""
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = secrets.token_hex(16)
    return user_id

def is_attack_payload(data):
    if not data:
        return None
    data_lower = data.lower()
    for pattern in ATTACK_PATTERNS:
        if re.search(pattern, data_lower, re.IGNORECASE):
            return True
    return False

def is_blocked(user_id):
    if user_id in blocked_users:
        if time.time() < blocked_users[user_id]:
            return True
        else:
            del blocked_users[user_id]
            if user_id in blocked_reasons:
                del blocked_reasons[user_id]
    return False

def get_block_reason(user_id):
    return blocked_reasons.get(user_id, "Atividade suspeita")

def block_user(user_id, reason, duration=BLOCK_TIME):
    blocked_users[user_id] = time.time() + duration
    blocked_reasons[user_id] = reason

def check_ip_block():
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                # Obter user_id ANTES de verificar bloqueio
                user_id = get_user_id()
                if is_blocked(user_id):
                    reason = get_block_reason(user_id)
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        motivo=reason, 
                                        tempo=f"{int((blocked_users[user_id] - time.time()) // 60)} minutos"), 403)
                    response.set_cookie('user_id', user_id, max_age=365*24*60*60, httponly=True, secure=True, samesite='Lax')
                    return response
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def register_failed_attempt(user_id, data, endpoint=""):
    """Regista uma tentativa para um utilizador específico."""
    # CASO 1: ATAQUE → bloqueia imediatamente
    if is_attack_payload(data):
        block_user(user_id, f"🚫 ATAQUE DETETADO: {data[:30]}...", ATTACK_BLOCK_TIME)
        return True
    
    # CASO 2: Erro normal → conta tentativas (apenas para este utilizador)
    now = time.time()
    failed_attempts[user_id] = [t for t in failed_attempts[user_id] if now - t < 300]
    failed_attempts[user_id].append(now)
    
    total = len(failed_attempts[user_id])
    
    # Só bloqueia após MUITAS tentativas (20) - apenas este utilizador
    if total >= 20:
        block_user(user_id, f"Muitas tentativas inválidas ({total})", BLOCK_TIME)
        return True
    
    return False
