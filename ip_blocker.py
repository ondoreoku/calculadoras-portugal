import time
import re
import secrets
from collections import defaultdict
from flask import request, jsonify, render_template, make_response

failed_attempts = defaultdict(list)
blocked_users = {}
blocked_reasons = {}

BLOCK_TIME = 900
ATTACK_BLOCK_TIME = 3600

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
    print(f"[BLOQUEIO] Utilizador {user_id[:8]} bloqueado: {reason}")

def check_ip_block():
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                user_id = get_user_id()
                
                if is_blocked(user_id):
                    reason = get_block_reason(user_id)
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        motivo=reason, 
                                        tempo=f"{int((blocked_users[user_id] - time.time()) // 60)} minutos"), 403)
                    response.set_cookie('user_id', user_id, max_age=365*24*60*60, httponly=True, secure=True, samesite='Lax')
                    return response
                
                form_data = list(request.form.values())
                all_data = " ".join(form_data)
                
                if is_attack_payload(all_data):
                    print(f"[BLOQUEIO] ATAQUE DETETADO! Bloqueando utilizador {user_id[:8]}")
                    block_user(user_id, f"🚫 ATAQUE DETETADO: {all_data[:50]}...", ATTACK_BLOCK_TIME)
                    
                    response = make_response(render_template("bloqueado.html", 
                                        user_id=user_id[:8],
                                        motivo="Tentativa de ataque detetada", 
                                        tempo="60 minutos"), 403)
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
    print(f"[DEBUG] Utilizador {user_id[:8]} - Erros normais: {total}")
    
    if total >= 20:
        block_user(user_id, f"Muitas tentativas inválidas ({total})", BLOCK_TIME)
        return True
    
    return False
