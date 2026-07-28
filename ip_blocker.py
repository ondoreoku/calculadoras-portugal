import time
import re
import secrets
from collections import defaultdict
from flask import request, jsonify, render_template, make_response
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estruturas de dados
failed_attempts = defaultdict(list)
blocked_users = {}  # user_id → timestamp
blocked_reasons = {}  # user_id → motivo
request_counts = defaultdict(list)  # user_id → lista de timestamps para rate limiting

# Configurações
BLOCK_TIME = 7200  # 2 horas (para erros normais)
ATTACK_BLOCK_TIME = 86400  # 24 horas (para ataques)
RATE_LIMIT = 10  # Máximo de pedidos por minuto
RATE_WINDOW = 60  # Janela de 60 segundos

# Padrões de ATAQUE
ATTACK_PATTERNS = [
    r'<script', r'javascript:', r'onerror=', r'alert\(', r'<iframe',
    r' UNION ', r' SELECT ', r' DROP ', r' DELETE ', r' INSERT ',
    r" OR '1'='1", r' OR 1=1', r'--', r';.*DROP', r'<img.*onerror',
    r'onload=', r'<body.*onload', r'<svg.*onload'
]

def get_user_id():
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = secrets.token_hex(16)
    return user_id

def is_attack_payload(data):
    if not data:
        return False
    data_lower = str(data).lower()
    for pattern in ATTACK_PATTERNS:
        if re.search(pattern, data_lower, re.IGNORECASE):
            return True
    return False

def is_blocked(user_id):
    if user_id in blocked_users:
        if time.time() < blocked_users[user_id]:
            return True, blocked_reasons.get(user_id, "Atividade suspeita")
        else:
            del blocked_users[user_id]
            if user_id in blocked_reasons:
                del blocked_reasons[user_id]
    return False, ""

def get_block_reason(user_id):
    return blocked_reasons.get(user_id, "Atividade suspeita")

def block_user(user_id, reason, duration=BLOCK_TIME):
    blocked_users[user_id] = time.time() + duration
    blocked_reasons[user_id] = reason
    logger.info(f"[BLOQUEIO] Utilizador {user_id[:8]} bloqueado: {reason}")

def check_rate_limit(user_id):
    """Verifica rate limiting para um utilizador."""
    now = time.time()
    # Limpar pedidos antigos
    request_counts[user_id] = [t for t in request_counts[user_id] if now - t < RATE_WINDOW]
    
    if len(request_counts[user_id]) >= RATE_LIMIT:
        block_user(user_id, f"Demasiados pedidos ({len(request_counts[user_id])} em 60s)", 300)  # Bloqueia 5 min
        return True
    
    request_counts[user_id].append(now)
    return False

def check_ip_block():
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                user_id = get_user_id()
                
                # Rate Limiting (NOVO!)
                if check_rate_limit(user_id):
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        motivo="Demasiados pedidos (rate limiting)", 
                                        tempo="5 minutos"), 429)
                    response.set_cookie('user_id', user_id, max_age=365*24*60*60, httponly=True, secure=True, samesite='Lax')
                    return response
                
                # Verificar bloqueio por utilizador (cookie)
                is_blocked_flag, reason = is_blocked(user_id)
                if is_blocked_flag:
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        motivo=reason, 
                                        tempo=f"{int((blocked_users[user_id] - time.time()) // 60)} minutos"), 403)
                    response.set_cookie('user_id', user_id, max_age=365*24*60*60, httponly=True, secure=True, samesite='Lax')
                    return response
                
                # Verificar se o pedido atual é um ataque
                form_data = list(request.form.values())
                all_data = " ".join(form_data)
                
                if is_attack_payload(all_data):
                    logger.info(f"[BLOQUEIO] ATAQUE DETETADO! Bloqueando utilizador {user_id[:8]}")
                    block_user(user_id, f"🚫 ATAQUE DETETADO: {all_data[:50]}...", ATTACK_BLOCK_TIME)
                    
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        motivo="Tentativa de ataque detetada", 
                                        tempo="24 horas"), 403)
                    response.set_cookie('user_id', user_id, max_age=365*24*60*60, httponly=True, secure=True, samesite='Lax')
                    return response
                
                return f(*args, **kwargs)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def register_failed_attempt(user_id, data, endpoint=""):
    if is_attack_payload(data):
        return True
    
    now = time.time()
    failed_attempts[user_id] = [t for t in failed_attempts[user_id] if now - t < 300]
    failed_attempts[user_id].append(now)
    
    total = len(failed_attempts[user_id])
    logger.info(f"[DEBUG] Utilizador {user_id[:8]} - Erros normais: {total}")
    
    if total >= 20:
        block_user(user_id, f"Muitas tentativas inválidas ({total})", BLOCK_TIME)
        return True
    
    return False
