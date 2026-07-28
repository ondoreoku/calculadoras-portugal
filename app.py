"""
================================================================================
APP.PY — Aplicação Flask Principal
================================================================================

O QUE FAZ:
    Servidor web Flask com rotas para todas as páginas do site.
    Integração com base de dados SQLite (notícias, histórico, taxas).
    Processamento de formulários das 4 calculadoras.

ROTAS:
    GET  /                    → Home page (com notícias do SQLite)
    GET  /salario             → Calculadora de Salário Líquido
    GET/POST /salario         → Processa formulário + mostra resultados
    GET  /credito             → Simulador de Crédito Habitação
    GET/POST /credito         → Processa formulário + mostra resultados
    GET  /rescisao            → Calculadora de Rescisão
    GET/POST /rescisao        → Processa formulário + mostra resultados
    GET/POST /subsidio        → Simulador de Subsídio Desemprego (funcional)
    GET  /atualizar_noticias  → Força atualização do feed RSS
    GET  /historico           → Histórico de cálculos

    --- ROTAS DA API (para frontends Vercel) ---
    POST /api/salario         → API para Salário Líquido
    POST /api/credito         → API para Crédito Habitação
    POST /api/rescisao        → API para Rescisão
    POST /api/subsidio        → API para Subsídio Desemprego
    GET  /api/health          → Health check

DEPENDÊNCIAS:
    — Flask: pip install flask
    — flask-cors: pip install flask-cors
    — feedparser: pip install feedparser (para notícias RSS)

COMO INICIAR:
    1. python3 initdb.py    (cria a base de dados — só uma vez)
    2. python3 app.py       (inicia o servidor)
    3. Abrir http://127.0.0.1:5000 no browser
================================================================================
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
from rate_limits import limiter
from security_logger import log_security_event, log_brute_force_attempt, log_invalid_input
import sqlite3
import json
import os
from datetime import datetime

# =============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# =============================================================================
app = Flask(__name__)

# =============================================================================
# RATE LIMITING
# =============================================================================
limiter.init_app(app)

# =============================================================================
# HEADERS DE SEGURANÇA
# =============================================================================
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdnjs.buymeacoffee.com; style-src 'self'; img-src 'self' data:; frame-src 'self'; object-src 'none'"
    return response

# =============================================================================
# CONFIGURAÇÃO CORS (apenas para os endpoints da API)
# =============================================================================
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://salarioliquido.vercel.app",
            "https://simulador-credito-habitacao-2026.vercel.app",
            "https://calculadora-rescisao-contrato.vercel.app",
            "https://simulador-subsidio-desemprego.vercel.app"
        ]
    }
})

# =============================================================================
# IMPORTS DOS MÓDULOS DE CÁLCULO
# =============================================================================
from utils.noticias import get_noticias, atualizar_noticias, limpar_cache_antigo
from utils.subsidio import calcular_subsidio
from utils.credito import calcular_credito, calcular_tabela_amortizacao
from utils.salario import calcular_salario
from utils.rescisao import calcular_rescisao

DATABASE = "database.db"

# =============================================================================
# FUNÇÃO DE VALIDAÇÃO DE INPUTS
# =============================================================================
def validar_numero(valor, nome="valor", min_val=0, max_val=1000000):
    try:
        num = float(valor)
        if num < min_val or num > max_val:
            return None, f"{nome} deve estar entre {min_val} e {max_val}"
        return num, None
    except ValueError:
        return None, f"{nome} inválido"

# =============================================================================
# INICIALIZAÇÃO AUTOMÁTICA DA BASE DE DADOS
# =============================================================================
def init_db_if_missing():
    """Cria a base de dados se não existir (necessário no Render)."""
    if not os.path.exists(DATABASE):
        print("[INFO] Base de dados não encontrada. A criar...")
        import initdb
        initdb.create_tables()
        initdb.seed_taxas()
        print("[INFO] A buscar notícias do RSS...")
        try:
            inseridas = atualizar_noticias()
            limpar_cache_antigo()
            print(f"[OK] {inseridas} notícias inseridas automaticamente")
        except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
            print(f"[AVISO] Não foi possível atualizar notícias: {e}")
        print("[OK] Base de dados criada com sucesso")

init_db_if_missing()

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def get_db():
    """Abre conexão com SQLite."""
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con

def guardar_historico(tipo, inputs_dict, resultado_dict):
    """Guarda um cálculo no histórico da base de dados."""
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO historico_calculos (tipo, input_json, resultado_json)
        VALUES (?, ?, ?)
    """, (
        tipo,
        json.dumps(inputs_dict, ensure_ascii=False),
        json.dumps(resultado_dict, ensure_ascii=False)
    ))
    con.commit()
    con.close()

# =============================================================================
# ROTAS HTML (PÁGINAS DO SITE)
# =============================================================================

@app.route("/")
def home():
    noticias = get_noticias(limite=9)
    return render_template("home.html", noticias=noticias)

@app.route("/atualizar_noticias")
def atualizar_noticias_rota():
    try:
        inseridas = atualizar_noticias()
        limpar_cache_antigo()
        print(f"[INFO] Atualização concluída: {inseridas} notícias novas")
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        print(f"[ERRO] Falha na atualização: {e}")
    return redirect(url_for("home"))

@app.route("/historico")
def historico():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT tipo, input_json, resultado_json, data_hora
        FROM historico_calculos
        ORDER BY data_hora DESC
        LIMIT 50
    """)
    rows = cur.fetchall()
    con.close()

    registos = []
    for row in rows:
        inputs = json.loads(row["input_json"]) if row["input_json"] else {}
        resultado = json.loads(row["resultado_json"]) if row["resultado_json"] else {}
        nomes_tipos = {
            "subsidio": "Subsídio Desemprego",
            "salario": "Salário Líquido",
            "credito": "Crédito Habitação",
            "rescisao": "Rescisão",
        }
        registos.append({
            "tipo": nomes_tipos.get(row["tipo"], row["tipo"]),
            "tipo_raw": row["tipo"],
            "inputs": inputs,
            "resultado": resultado,
            "data_hora": row["data_hora"],
        })
    return render_template("historico.html", registos=registos)

@app.route("/salario", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def salario():
    resultado = None
    regime = "outrem"
    bruto = 1500
    subsidio_alimentacao = 6.0
    estado_civil = "solteiro"
    coeficiente_atividade = 0.75
    retencao_irs = 0.15
    isento_ss = "nao"
    erro = None

    if request.method == "POST":
        regime = request.form.get("regime", "outrem")
        bruto, erro = validar_numero(request.form.get("bruto", 0), "Salário")
        
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("salario.html", 
                                erro=erro,
                                regime=regime,
                                bruto=bruto if bruto else 0,
                                subsidio_alimentacao=subsidio_alimentacao,
                                estado_civil=estado_civil,
                                coeficiente_atividade=coeficiente_atividade,
                                retencao_irs=retencao_irs,
                                isento_ss=isento_ss)

        if regime == "outrem":
            subsidio_alimentacao, erro = validar_numero(request.form.get("subsidio_alimentacao", 0), "Subsídio alimentação")
            if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
                return render_template("salario.html", erro=erro)
            estado_civil = request.form.get("estado_civil", "solteiro")
            resultado = calcular_salario(
            log_security_event("CALCULO_SALARIO", request.remote_addr, f"Bruto: {bruto}")
                bruto=bruto,
                regime="outrem",
                subsidio_alimentacao=subsidio_alimentacao,
                estado_civil=estado_civil
            )
        else:
            coeficiente_atividade, erro = validar_numero(request.form.get("coeficiente_atividade", 0.75), "Coeficiente de atividade", 0, 1)
            if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
                return render_template("salario.html", erro=erro)
            retencao_irs, erro = validar_numero(request.form.get("retencao_irs", 0.15), "Retenção IRS", 0, 1)
            if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
                return render_template("salario.html", erro=erro)
            isento_ss = request.form.get("isento_ss", "nao")
            resultado = calcular_salario(
            log_security_event("CALCULO_SALARIO", request.remote_addr, f"Bruto: {bruto}")
                bruto=bruto,
                regime="eni",
                coeficiente_atividade=coeficiente_atividade,
                retencao_irs=retencao_irs,
                isento_ss=isento_ss
            )

        guardar_historico(
            tipo="salario",
            inputs_dict={
                "bruto": bruto,
                "regime": regime,
                "subsidio_alimentacao": subsidio_alimentacao if regime == "outrem" else 0,
                "estado_civil": estado_civil if regime == "outrem" else "",
                "coeficiente_atividade": coeficiente_atividade if regime == "eni" else 0,
                "retencao_irs": retencao_irs if regime == "eni" else 0,
                "isento_ss": isento_ss if regime == "eni" else "",
            },
            resultado_dict=resultado
        )

    return render_template("salario.html",
                          resultado=resultado,
                          erro=erro,
                          regime=regime,
                          bruto=bruto,
                          subsidio_alimentacao=subsidio_alimentacao,
                          estado_civil=estado_civil,
                          coeficiente_atividade=coeficiente_atividade,
                          retencao_irs=retencao_irs,
                          isento_ss=isento_ss)

@app.route("/credito", methods=["GET", "POST"])
def credito():
    resultado = None
    tabela = None
    erro = None

    if request.method == "POST":
        valor_imovel, erro = validar_numero(request.form.get("valor_imovel", 0), "Valor do imóvel")
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("credito.html", erro=erro)
            
        entrada, erro = validar_numero(request.form.get("entrada", 0), "Entrada")
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("credito.html", erro=erro)
            
        prazo_anos, erro = validar_numero(request.form.get("prazo_anos", 0), "Prazo", 1, 50)
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("credito.html", erro=erro)
        prazo_anos = int(prazo_anos)
        
        spread, erro = validar_numero(request.form.get("spread", 0), "Spread", 0, 100)
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("credito.html", erro=erro)
            
        euribor, erro = validar_numero(request.form.get("euribor", 0), "Euribor", -100, 100)
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("credito.html", erro=erro)

        resultado = calcular_credito(valor_imovel, entrada, prazo_anos, spread, euribor)
        tabela = calcular_tabela_amortizacao(valor_imovel, entrada, prazo_anos, spread, euribor, limite=12)

        guardar_historico(
            tipo="credito",
            inputs_dict={
                "valor_imovel": valor_imovel,
                "entrada": entrada,
                "prazo_anos": prazo_anos,
                "spread": spread,
                "euribor": euribor
            },
            resultado_dict=resultado
        )

    return render_template("credito.html", resultado=resultado, tabela=tabela, erro=erro)

@app.route("/rescisao", methods=["GET", "POST"])
def rescisao():
    resultado = None
    erro = None
    vencimento_base = 1200
    subsidio_alimentacao = 6.0
    data_inicio = "2020-01-15"
    data_fim = "2026-07-16"
    motivo = "caducidade_termo"
    meses_layoff = 0
    ferias_vencidas = 0
    horas_formacao = 0

    if request.method == "POST":
        vencimento_base, erro = validar_numero(request.form.get("vencimento_base", 0), "Vencimento base")
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("rescisao.html", erro=erro)
            
        subsidio_alimentacao, erro = validar_numero(request.form.get("subsidio_alimentacao", 0), "Subsídio alimentação")
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("rescisao.html", erro=erro)
            
        data_inicio = request.form.get("data_inicio", "")
        data_fim = request.form.get("data_fim", "")
        motivo = request.form.get("motivo", "caducidade_termo")
        meses_layoff, erro = validar_numero(request.form.get("meses_layoff", 0), "Meses em lay-off", 0, 100)
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("rescisao.html", erro=erro)
        meses_layoff = int(meses_layoff)
        
        ferias_vencidas, erro = validar_numero(request.form.get("ferias_vencidas", 0), "Férias vencidas", 0, 1000)
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("rescisao.html", erro=erro)
        ferias_vencidas = int(ferias_vencidas)
        
        horas_formacao, erro = validar_numero(request.form.get("horas_formacao", 0), "Horas de formação", 0, 1000)
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("rescisao.html", erro=erro)
        horas_formacao = int(horas_formacao)

        resultado = calcular_rescisao(
            vencimento_base=vencimento_base,
            subsidio_alimentacao=subsidio_alimentacao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            motivo=motivo,
            meses_layoff=meses_layoff,
            ferias_vencidas=ferias_vencidas,
            horas_formacao=horas_formacao
        )

        guardar_historico(
            tipo="rescisao",
            inputs_dict={
                "vencimento_base": vencimento_base,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "motivo": motivo
            },
            resultado_dict=resultado
        )

    return render_template("rescisao.html",
                          resultado=resultado,
                          erro=erro,
                          vencimento_base=vencimento_base,
                          subsidio_alimentacao=subsidio_alimentacao,
                          data_inicio=data_inicio,
                          data_fim=data_fim,
                          motivo=motivo,
                          meses_layoff=meses_layoff,
                          ferias_vencidas=ferias_vencidas,
                          horas_formacao=horas_formacao)

@app.route("/subsidio", methods=["GET", "POST"])
def subsidio():
    resultado = None
    erro = None

    if request.method == "POST":
        media_salarial, erro = validar_numero(request.form.get("media_salarial", 0), "Média salarial")
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("subsidio.html", erro=erro)
            
        idade, erro = validar_numero(request.form.get("idade", 0), "Idade", 16, 100)
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("subsidio.html", erro=erro)
        idade = int(idade)
        
        meses_desconto, erro = validar_numero(request.form.get("meses_desconto", 0), "Meses de desconto", 0, 999)
        if erro:
            log_invalid_input(request.remote_addr, "/salario", request.form.get("bruto", ""))
            return render_template("subsidio.html", erro=erro)
        meses_desconto = int(meses_desconto)

        resultado = calcular_subsidio(media_salarial, idade, meses_desconto)

        guardar_historico(
            tipo="subsidio",
            inputs_dict={
                "media_salarial": media_salarial,
                "idade": idade,
                "meses_desconto": meses_desconto
            },
            resultado_dict=resultado
        )

    return render_template("subsidio.html", resultado=resultado, erro=erro)

# =============================================================================
# ROTAS DA API (para os frontends da Vercel)
# =============================================================================

@app.route("/api/salario", methods=["POST"])
@limiter.limit("10 per minute")
def api_salario():
    try:
        dados = request.get_json()
        if not dados or "bruto" not in dados:
            return jsonify({"erro": "Dados inválidos."}), 400
        if dados.get("regime") == "eni":
            resultado = calcular_salario(
            log_security_event("CALCULO_SALARIO", request.remote_addr, f"Bruto: {bruto}")
                bruto=dados["bruto"],
                regime="eni",
                coeficiente_atividade=dados.get("coeficiente_atividade", 0.75),
                retencao_irs=dados.get("retencao_irs", 0.15),
                isento_ss=dados.get("isento_ss", "nao")
            )
        else:
            resultado = calcular_salario(
            log_security_event("CALCULO_SALARIO", request.remote_addr, f"Bruto: {bruto}")
                bruto=dados["bruto"],
                regime="outrem",
                subsidio_alimentacao=dados.get("subsidio_alimentacao", 6.0),
                estado_civil=dados.get("estado_civil", "solteiro")
            )
        guardar_historico(tipo="salario", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        return jsonify({"erro": str(e)}), 500

@app.route("/api/credito", methods=["POST"])
def api_credito():
    try:
        dados = request.get_json()
        if not dados or "valor_imovel" not in dados:
            return jsonify({"erro": "Dados inválidos."}), 400
        resultado = calcular_credito(
            dados["valor_imovel"],
            dados.get("entrada", 0),
            dados.get("prazo_anos", 30),
            dados.get("spread", 1.0),
            dados.get("euribor", 3.5)
        )
        guardar_historico(tipo="credito", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        return jsonify({"erro": str(e)}), 500

@app.route("/api/rescisao", methods=["POST"])
def api_rescisao():
    try:
        dados = request.get_json()
        if not dados or "vencimento_base" not in dados:
            return jsonify({"erro": "Dados inválidos."}), 400
        resultado = calcular_rescisao(
            vencimento_base=dados["vencimento_base"],
            subsidio_alimentacao=dados.get("subsidio_alimentacao", 6.0),
            data_inicio=dados.get("data_inicio", "2020-01-01"),
            data_fim=dados.get("data_fim", "2026-01-01"),
            motivo=dados.get("motivo", "caducidade_termo"),
            meses_layoff=int(dados.get("meses_layoff", 0)),
            ferias_vencidas=int(dados.get("ferias_vencidas", 0)),
            horas_formacao=int(dados.get("horas_formacao", 0))
        )
        guardar_historico(tipo="rescisao", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        return jsonify({"erro": str(e)}), 500

@app.route("/api/subsidio", methods=["POST"])
def api_subsidio():
    try:
        dados = request.get_json()
        if not dados or "media_salarial" not in dados:
            return jsonify({"erro": "Dados inválidos."}), 400
        resultado = calcular_subsidio(
            dados["media_salarial"],
            int(dados.get("idade", 30)),
            int(dados.get("meses_desconto", 12))
        )
        guardar_historico(tipo="subsidio", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        return jsonify({"erro": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "API Calculadoras Portugal 2026"})

# =============================================================================
# TRATAMENTO DE ERROS
# =============================================================================
@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500

@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Página não encontrada</h1><p><a href='/'>Voltar ao início</a></p>", 404

# =============================================================================
# INICIALIZAÇÃO DO SERVIDOR
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Calculadoras Portugal 2026")
    print("  Servidor Flask a iniciar...")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
