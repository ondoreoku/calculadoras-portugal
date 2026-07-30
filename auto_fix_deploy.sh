#!/bin/bash
# ========================================================================
# AUTO-FIX DEPLOY - Calculadoras Portugal 2026
# Corrige automaticamente todos os problemas e faz deploy
# ========================================================================

set -e  # Para o script se algum comando falhar

echo "=========================================="
echo "🚀 AUTO-FIX DEPLOY"
echo "Calculadoras Portugal 2026"
echo "=========================================="
echo ""

# ========================================================================
# 1. BACKUP DOS FICHEIROS
# ========================================================================
echo "📦 1. Criando backups..."
mkdir -p backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp app.py backups/app.py.$TIMESTAMP
cp ip_blocker.py backups/ip_blocker.py.$TIMESTAMP
cp static/css/style.css backups/style.css.$TIMESTAMP
echo "✅ Backups criados em backups/*.$TIMESTAMP"
echo ""

# ========================================================================
# 2. CORRIGIR IP_BLOCKER.PY (indentação)
# ========================================================================
echo "🔧 2. Corrigindo ip_blocker.py..."
cat > ip_blocker.py << 'IPEOF'
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
IPEOF
echo "✅ ip_blocker.py corrigido"
echo ""

# ========================================================================
# 3. CORRIGIR RENDER.YAML (adicionar dependências do weasyprint)
# ========================================================================
echo "🔧 3. Corrigindo render.yaml..."
cat > render.yaml << 'RENDEREOF'
services:
  - type: web
    name: calculadoras-portugal-2026
    runtime: python
    plan: free
    buildCommand: |
      apt-get update && apt-get install -y \
        build-essential \
        python3-dev \
        libpango1.0-dev \
        libpangoft2-1.0-0 \
        libharfbuzz-dev \
        libfreetype-dev \
        libffi-dev \
        libjpeg-dev \
        libopenjp2-7 \
        libtiff-dev \
        && pip install -r requirements.txt
    startCommand: "gunicorn app:app"
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: FLASK_ENV
        value: production
RENDEREOF
echo "✅ render.yaml corrigido"
echo ""

# ========================================================================
# 4. CORRIGIR UTILS/PDF.PY (mais robusto)
# ========================================================================
echo "🔧 4. Corrigindo utils/pdf.py..."
cat > utils/pdf.py << 'PDFEOF'
from weasyprint import HTML, CSS
from jinja2 import Template
from datetime import datetime
import os

def gerar_pdf_resultado(tipo, inputs, resultado):
    template_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Calculadora {{ tipo }}</title>
        <style>
            body { 
                font-family: Arial, Helvetica, sans-serif; 
                margin: 40px; 
                background: #f9fafb;
                color: #1f2937;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 12px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            }
            h1 { 
                color: #059669; 
                border-bottom: 3px solid #059669; 
                padding-bottom: 10px; 
                font-size: 24px;
            }
            .resultado { 
                background: #f0fdf4; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 20px 0; 
                border-left: 4px solid #059669; 
            }
            .dados { 
                background: #f9fafb; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 20px 0; 
            }
            .footer { 
                margin-top: 30px; 
                padding-top: 20px; 
                border-top: 1px solid #e5e7eb; 
                font-size: 12px; 
                color: #6b7280; 
                text-align: center; 
            }
            .label { 
                font-weight: 600; 
                color: #374151; 
            }
            .valor { 
                color: #059669; 
                font-weight: 700; 
            }
            .linha {
                margin: 8px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Calculadora de {{ tipo }}</h1>
            <p><strong>Data:</strong> {{ data }}</p>
            
            <div class="resultado">
                <h2 style="font-size:18px; margin-top:0;">📈 Resultado</h2>
                {% for key, value in resultado.items() %}
                <p class="linha"><span class="label">{{ key }}:</span> <span class="valor">{{ value }}</span></p>
                {% endfor %}
            </div>
            
            <div class="dados">
                <h3 style="font-size:16px; margin-top:0;">📋 Dados de Entrada</h3>
                {% for key, value in inputs.items() %}
                <p class="linha"><span class="label">{{ key }}:</span> {{ value }}</p>
                {% endfor %}
            </div>
            
            <div class="footer">
                <p>Calculadoras Portugal 2026</p>
                <p>https://calculadoras-portugal.onrender.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        html = Template(template_html).render(
            tipo=tipo, 
            data=datetime.now().strftime("%d/%m/%Y às %H:%M"), 
            inputs=inputs, 
            resultado=resultado
        )
        
        pdf = HTML(string=html).write_pdf(
            stylesheets=[CSS(string='@page { margin: 1cm; }')]
        )
        
        if pdf and len(pdf) > 100:
            return pdf
        else:
            print(f"[ERRO PDF] PDF gerado tem apenas {len(pdf) if pdf else 0} bytes")
            return None
            
    except Exception as e:
        print(f"[ERRO PDF] Falha ao gerar PDF: {str(e)}")
        return None
PDFEOF
echo "✅ utils/pdf.py corrigido"
echo ""

# ========================================================================
# 5. CORRIGIR CSS (dark mode da página de bloqueio)
# ========================================================================
echo "🔧 5. Corrigindo CSS (dark mode)..."
cat >> static/css/style.css << 'CSSEOF'

/* DARK MODE - PÁGINA DE BLOQUEIO */
.dark-mode .bloqueio-container h1 {
    color: #f87171 !important;
}

.dark-mode .bloqueio-container p {
    color: #c8c8d8 !important;
}

.dark-mode .bloqueio-box {
    background-color: #2d2d44 !important;
    border-color: #4a4a6a !important;
    color: #e8e8e8 !important;
}

.dark-mode .bloqueio-box strong {
    color: #e8e8e8 !important;
}

.dark-mode .bloqueio-box p {
    color: #c8c8d8 !important;
}
CSSEOF
echo "✅ CSS corrigido"
echo ""

# ========================================================================
# 6. ADICIONAR ROTAS PDF AO APP.PY (SE FALTAREM)
# ========================================================================
echo "🔧 6. Verificando rotas PDF no app.py..."

if ! grep -q "@app.route(\"/salario/pdf\"" app.py; then
    echo "Adicionando rotas PDF..."
    cat >> app.py << 'APPEOF'

# =============================================================================
# ROTAS PDF PARA TODAS AS CALCULADORAS
# =============================================================================

@app.route("/salario/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def salario_pdf():
    """Gera PDF com o cálculo do salário"""
    try:
        bruto = request.args.get("salario_bruto", type=float)
        regime = request.args.get("regime", "outrem")
        
        if not bruto:
            return jsonify({"erro": "Parâmetro salario_bruto obrigatório"}), 400
        
        if regime == "eni":
            resultado = calcular_salario(
                bruto=bruto,
                regime="eni",
                coeficiente_atividade=0.75,
                retencao_irs=0.15,
                isento_ss="nao"
            )
            inputs = {"Salário Bruto": f"€{bruto:.2f}", "Regime": "Trabalhador Independente (ENI)"}
        else:
            resultado = calcular_salario(
                bruto=bruto,
                regime="outrem",
                subsidio_alimentacao=6.0,
                estado_civil="solteiro"
            )
            inputs = {"Salário Bruto": f"€{bruto:.2f}", "Regime": "Conta de Outrem"}
        
        pdf = gerar_pdf_resultado("Salário Líquido", inputs, resultado)
        
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=salario_{bruto:.0f}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        import traceback
        print(f"[ERRO PDF SALARIO] {traceback.format_exc()}")
        return jsonify({"erro": str(e)}), 500


@app.route("/credito/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def credito_pdf():
    """Gera PDF com o cálculo do crédito habitação"""
    try:
        valor_imovel = request.args.get("valor_imovel", type=float)
        entrada = request.args.get("entrada", type=float, default=0)
        prazo_anos = request.args.get("prazo_anos", type=int, default=30)
        spread = request.args.get("spread", type=float, default=1.5)
        euribor = request.args.get("euribor", type=float, default=3.5)
        
        if not valor_imovel:
            return jsonify({"erro": "Parâmetro valor_imovel obrigatório"}), 400
        
        resultado = calcular_credito(valor_imovel, entrada, prazo_anos, spread, euribor)
        inputs = {
            "Valor do Imóvel": f"€{valor_imovel:.2f}",
            "Entrada": f"€{entrada:.2f}",
            "Prazo": f"{prazo_anos} anos",
            "Spread": f"{spread}%",
            "Euribor": f"{euribor}%"
        }
        
        pdf = gerar_pdf_resultado("Crédito Habitação", inputs, resultado)
        
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=credito_{valor_imovel:.0f}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        import traceback
        print(f"[ERRO PDF CREDITO] {traceback.format_exc()}")
        return jsonify({"erro": str(e)}), 500


@app.route("/rescisao/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def rescisao_pdf():
    """Gera PDF com o cálculo da rescisão"""
    try:
        vencimento_base = request.args.get("vencimento_base", type=float)
        subsidio_alimentacao = request.args.get("subsidio_alimentacao", type=float, default=6.0)
        data_inicio = request.args.get("data_inicio", "2020-01-15")
        data_fim = request.args.get("data_fim", "2026-07-16")
        motivo = request.args.get("motivo", "caducidade_termo")
        
        if not vencimento_base:
            return jsonify({"erro": "Parâmetro vencimento_base obrigatório"}), 400
        
        resultado = calcular_rescisao(
            vencimento_base=vencimento_base,
            subsidio_alimentacao=subsidio_alimentacao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            motivo=motivo
        )
        inputs = {
            "Vencimento Base": f"€{vencimento_base:.2f}",
            "Subsídio Alimentação": f"€{subsidio_alimentacao:.2f}/dia",
            "Data Início": data_inicio,
            "Data Fim": data_fim,
            "Motivo": motivo
        }
        
        pdf = gerar_pdf_resultado("Rescisão de Contrato", inputs, resultado)
        
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=rescisao_{vencimento_base:.0f}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        import traceback
        print(f"[ERRO PDF RESCISAO] {traceback.format_exc()}")
        return jsonify({"erro": str(e)}), 500


@app.route("/subsidio/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def subsidio_pdf():
    """Gera PDF com o cálculo do subsídio de desemprego"""
    try:
        media_salarial = request.args.get("media_salarial", type=float)
        idade = request.args.get("idade", type=int, default=30)
        meses_desconto = request.args.get("meses_desconto", type=int, default=12)
        
        if not media_salarial:
            return jsonify({"erro": "Parâmetro media_salarial obrigatório"}), 400
        
        resultado = calcular_subsidio(media_salarial, idade, meses_desconto)
        inputs = {
            "Média Salarial": f"€{media_salarial:.2f}",
            "Idade": f"{idade} anos",
            "Meses de Desconto": f"{meses_desconto} meses"
        }
        
        pdf = gerar_pdf_resultado("Subsídio de Desemprego", inputs, resultado)
        
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=subsidio_{media_salarial:.0f}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        import traceback
        print(f"[ERRO PDF SUBSIDIO] {traceback.format_exc()}")
        return jsonify({"erro": str(e)}), 500
APPEOF
    echo "✅ Rotas PDF adicionadas"
else
    echo "✅ Rotas PDF já existem"
fi
echo ""

# ========================================================================
# 7. VERIFICAR SINTAXE
# ========================================================================
echo "🔍 7. Verificando sintaxe do Python..."
python3 -m py_compile app.py || { echo "❌ Erro de sintaxe no app.py"; exit 1; }
python3 -m py_compile ip_blocker.py || { echo "❌ Erro de sintaxe no ip_blocker.py"; exit 1; }
python3 -m py_compile utils/pdf.py || { echo "❌ Erro de sintaxe no utils/pdf.py"; exit 1; }
echo "✅ Sintaxe OK"
echo ""

# ========================================================================
# 8. COMMIT E PUSH
# ========================================================================
echo "📤 8. Fazendo commit e push..."
git add app.py ip_blocker.py render.yaml utils/pdf.py static/css/style.css
git commit -m "Auto-fix: Correções automáticas - $(date '+%Y-%m-%d %H:%M:%S')" || echo "Nada para commitar"
git push origin CYBERSEC
echo "✅ Commit e push feitos!"
echo ""

# ========================================================================
# 9. TESTAR DEPLOY
# ========================================================================
echo "🧪 9. Testando deploy..."
echo "Aguardando 10 segundos para o deploy iniciar..."
sleep 10

echo ""
echo "Testando health check..."
curl -s -o /dev/null -w "Health: %{http_code}\n" https://calculadoras-portugal.onrender.com/api/health

echo ""
echo "Testando PDF Salário..."
curl -s -o /dev/null -w "PDF Salário: %{http_code}\n" "https://calculadoras-portugal.onrender.com/salario/pdf?salario_bruto=1500"

echo ""
echo "Testando API INE..."
curl -s -o /dev/null -w "API INE: %{http_code}\n" https://calculadoras-portugal.onrender.com/api/ine/inflacao

echo ""
echo "Testando API Carros ISV..."
curl -s -o /dev/null -w "API Carros ISV: %{http_code}\n" "https://calculadoras-portugal.onrender.com/api/carros/isv?ano=2020&cilindrada=2000&co2=150"

echo ""
echo "=========================================="
echo "✅ AUTO-FIX CONCLUÍDO!"
echo "=========================================="
echo ""
echo "📊 Resumo:"
echo "  ✅ ip_blocker.py corrigido"
echo "  ✅ render.yaml corrigido (dependências weasyprint)"
echo "  ✅ utils/pdf.py corrigido"
echo "  ✅ CSS dark mode corrigido"
echo "  ✅ Rotas PDF adicionadas (se faltavam)"
echo "  ✅ Commit e push feitos"
echo ""
echo "🔍 Verifica o deploy no Render:"
echo "   https://dashboard.render.com"
echo ""
