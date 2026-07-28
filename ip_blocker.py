import time
from collections import defaultdict
from flask import request, jsonify, render_template

failed_attempts = defaultdict(list)
blocked_ips = {}
blocked_reasons = {}

BLOCK_TIME = 900
ATTEMPTS_LIMIT = 5
XSS_LIMIT = 3
SQL_LIMIT = 3

def is_blocked(ip):
    if ip in blocked_ips:
        if time.time() < blocked_ips[ip]:
            return True
        else:
            del blocked_ips[ip]
            if ip in blocked_reasons:
                del blocked_reasons[ip]
    return False

def get_block_reason(ip):
    return blocked_reasons.get(ip, "Atividade suspeita")

def block_ip(ip, reason, duration=BLOCK_TIME):
    blocked_ips[ip] = time.time() + duration
    blocked_reasons[ip] = reason

def check_ip_block():
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr or '127.0.0.1'
            if is_blocked(ip):
                reason = get_block_reason(ip)
                return render_template("bloqueado.html", ip=ip, motivo=reason, tempo=f"{int((blocked_ips[ip] - time.time()) // 60)} minutos"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def register_failed_attempt(ip, attempt_type="invalid_input"):
    now = time.time()
    failed_attempts[ip] = [t for t in failed_attempts[ip] if now - t < 300]
    failed_attempts[ip].append(now)
    total_attempts = len(failed_attempts[ip])
    
    if attempt_type == "xss" and total_attempts >= XSS_LIMIT:
        block_ip(ip, f"Tentativas de XSS ({total_attempts})", 1800)
    elif attempt_type == "sql" and total_attempts >= SQL_LIMIT:
        block_ip(ip, f"Tentativas de SQL Injection ({total_attempts})", 1800)
    elif total_attempts >= ATTEMPTS_LIMIT:
        block_ip(ip, f"Muitas tentativas inválidas ({total_attempts})", BLOCK_TIME)
