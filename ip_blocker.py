import time
import re
from collections import defaultdict
from flask import request, jsonify, render_template

# Estruturas de dados
failed_attempts = defaultdict(list)
blocked_ips = {}
blocked_reasons = {}

# Configurações
BLOCK_TIME = 900  # 15 minutos para erros normais
ATTACK_BLOCK_TIME = 3600  # 1 hora para ataques confirmados

# Padrões de ATAQUE (XSS, SQLi, etc.)
ATTACK_PATTERNS = [
    r'<script', r'javascript:', r'onerror=', r'alert\(', r'<iframe',
    r' UNION ', r' SELECT ', r' DROP ', r' DELETE ', r' INSERT ',
    r" OR '1'='1", r' OR 1=1', r'--', r';.*DROP', r'<img.*onerror'
]

def is_attack_payload(data):
    """Verifica se o input contém um padrão de ataque."""
    if not data:
        return None
    data_lower = data.lower()
    for pattern in ATTACK_PATTERNS:
        if re.search(pattern, data_lower, re.IGNORECASE):
            return True
    return False

def is_blocked(ip):
    """Verifica se um IP está bloqueado."""
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
            if request.method == 'POST':
                ip = request.remote_addr or '127.0.0.1'
                if is_blocked(ip):
                    reason = get_block_reason(ip)
                    return render_template("bloqueado.html", 
                                         ip=ip, 
                                         motivo=reason, 
                                         tempo=f"{int((blocked_ips[ip] - time.time()) // 60)} minutos"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def register_failed_attempt(ip, data, endpoint=""):
    """
    Regista uma tentativa.
    - Se for ATAQUE (XSS/SQLi) → bloqueia IMEDIATAMENTE por 1 hora
    - Se for erro normal (ex: "teste") → apenas conta, só bloqueia após MUITAS (20)
    """
    # CASO 1: ATAQUE CONFIRMADO → bloqueia imediatamente
    if is_attack_payload(data):
        block_ip(ip, f"🚫 ATAQUE DETETADO: {data[:30]}...", ATTACK_BLOCK_TIME)
        return True
    
    # CASO 2: Erro normal (ex: "teste", campo vazio) → conta tentativas
    now = time.time()
    failed_attempts[ip] = [t for t in failed_attempts[ip] if now - t < 300]  # limpa tentativas antigas
    failed_attempts[ip].append(now)
    
    total = len(failed_attempts[ip])
    
    # Só bloqueia após MUITAS tentativas (20) - para não prejudicar utilizadores legítimos
    if total >= 20:
        block_ip(ip, f"Muitas tentativas inválidas ({total})", BLOCK_TIME)
        return True
    
    return False
