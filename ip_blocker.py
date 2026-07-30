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
ip_request_counts = defaultdict(list)  # ip → lista de timestamps
ip_blocked = {}  # ip → timestamp (para rate limiting)
ip_block_reasons = {}  # ip → motivo

# Configurações
BLOCK_TIME = 7200  # 2 horas (para erros normais)
ATTACK_BLOCK_TIME = 86400  # 24 horas (para ataques)
RATE_LIMIT = 10  # Máximo de pedidos por minuto

# RATE LIMITING POR ENDPOINT
RATE_LIMITS = {
    "/salario": 10,
    "/credito": 10,
    "/rescisao": 10,
    "/subsidio": 10,
    "/api/salario": 20,
    "/api/credito": 20,
    "/api/rescisao": 20,
    "/api/subsidio": 20,
}

def get_rate_limit_for_endpoint(path):
    for endpoint, limit in RATE_LIMITS.items():
        if path.startswith(endpoint):
            return limit
    return RATE_LIMIT

RATE_WINDOW = 60
RATE_BLOCK_TIME = 300
RATE_BLOCK_ESCALATION = 3600

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

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

def is_attack_payload(data):
    if not data:
        return False
    data_lower = str(data).lower()
    for pattern in ATTACK_PATTERNS:
        if re.search(pattern, data_lower, re.IGNORECASE):
            return True
    return False

def is_blocked(user_id, ip):
    if ip in ip_blocked:
        if time.time() < ip_blocked[ip]:
            return True, ip_block_reasons.get(ip, "Demasiados pedidos")
        else:
            del ip_blocked[ip]
            if ip in ip_block_reasons:
                del ip_block_reasons[ip]
    
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

def check_rate_limit(ip):
    now = time.time()
    ip_request_counts[ip] = [t for t in ip_request_counts[ip] if now - t < RATE_WINDOW]
    
    path = request.path
    limit = get_rate_limit_for_endpoint(path)
    if len(ip_request_counts[ip]) >= limit:
        if ip in ip_blocked:
            duration = RATE_BLOCK_ESCALATION
            reason = f"Demasiados pedidos (reincidente) - {len(ip_request_counts[ip])} em 60s"
        else:
            duration = RATE_BLOCK_TIME
            reason = f"Demasiados pedidos ({len(ip_request_counts[ip])} em 60s)"
        
        ip_blocked[ip] = time.time() + duration
        ip_block_reasons[ip] = reason
        logger.warning(f"[RATE LIMIT] IP {ip} bloqueado: {reason} ({duration//60} min)")
        return True, reason, duration
    
    ip_request_counts[ip].append(now)
    return False, "", 0

def check_ip_block():
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                user_id = get_user_id()
                ip = get_client_ip()
                
                rate_limited, rate_reason, rate_duration = check_rate_limit(ip)
                if rate_limited:
                    minutes = rate_duration // 60
                    response = make_response(render_template("bloqueado.html", 
                                        user_id="IP",
                                        motivo=rate_reason, 
                                        tempo=f"{minutes} minutos"), 429)
                    return response
                
                is_blocked_flag, reason = is_blocked(user_id, ip)
                if is_blocked_flag:
                    if user_id in blocked_users:
                        minutes = int((blocked_users[user_id] - time.time()) // 60)
                        tempo = f"{minutes} minutos"
                    else:
                        tempo = "vários minutos"
                    
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        motivo=reason, 
                                        tempo=tempo), 403)
                    response.set_cookie('user_id', user_id, max_age=365*24*60*60, httponly=True, secure=True, samesite='Lax')
                    return response
                
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
