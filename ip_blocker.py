import time
import re
import secrets
from collections import defaultdict
from flask import request, jsonify, render_template, make_response

# Estruturas de dados
failed_attempts = defaultdict(list)
blocked_users = {}  # user_id → timestamp
blocked_ips = {}    # ip → timestamp

# Configurações
BLOCK_TIME = 900  # 15 minutos
ATTACK_BLOCK_TIME = 3600  # 1 hora
IP_BLOCK_TIME = 7200  # 2 horas

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

def is_blocked(user_id, ip):
    # Verificar bloqueio por IP
    if ip in blocked_ips:
        if time.time() < blocked_ips[ip]:
            return True, "IP bloqueado por atividade suspeita"
        else:
            del blocked_ips[ip]
    
    # Verificar bloqueio por utilizador (cookie)
    if user_id in blocked_users:
        if time.time() < blocked_users[user_id]:
            return True, blocked_users.get(user_id, "Atividade suspeita")
        else:
            del blocked_users[user_id]
    
    return False, ""

def block_user(user_id, ip, reason, duration=BLOCK_TIME):
    # Bloquear o utilizador (cookie)
    blocked_users[user_id] = time.time() + duration
    # Bloquear também o IP (prevenção)
    blocked_ips[ip] = time.time() + IP_BLOCK_TIME
    print(f"[BLOQUEIO] Utilizador {user_id[:8]} e IP {ip} bloqueados: {reason}")

def check_ip_block():
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                user_id = get_user_id()
                ip = request.remote_addr or '127.0.0.1'
                
                # Verificar bloqueio
                is_blocked_flag, reason = is_blocked(user_id, ip)
                if is_blocked_flag:
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        ip=ip,
                                        motivo=reason, 
                                        tempo="60 minutos"), 403)
                    response.set_cookie('user_id', user_id, max_age=365*24*60*60, httponly=True, secure=True, samesite='Lax')
                    return response
                
                # Verificar se o pedido atual é um ataque
                form_data = list(request.form.values())
                all_data = " ".join(form_data)
                
                if is_attack_payload(all_data):
                    print(f"[BLOQUEIO] ATAQUE DETETADO! Bloqueando utilizador {user_id[:8]} e IP {ip}")
                    block_user(user_id, ip, f"🚫 ATAQUE DETETADO: {all_data[:50]}...", ATTACK_BLOCK_TIME)
                    
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        ip=ip,
                                        motivo="Tentativa de ataque detetada", 
                                        tempo="60 minutos"), 403)
                    response.set_cookie('user_id', user_id, max_age=365*24*60*60, httponly=True, secure=True, samesite='Lax')
                    return response
                
                # Se chegou aqui, o pedido é seguro
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
    print(f"[DEBUG] Utilizador {user_id[:8]} - Erros normais: {total}")
    
    if total >= 20:
        ip = request.remote_addr or '127.0.0.1'
        block_user(user_id, ip, f"Muitas tentativas inválidas ({total})", BLOCK_TIME)
        return True
    
    return False
