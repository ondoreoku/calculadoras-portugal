from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import make_response
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)

# =============================================================================
# HEADERS DE SEGURANÇA
# =============================================================================
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self' https://*.buymeacoffee.com; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.buymeacoffee.com https://www.buymeacoffee.com https://cdn.jsdelivr.net https://*.buymeacoffee.com; style-src 'self' 'unsafe-inline' https://*.buymeacoffee.com; img-src 'self' data: https://*.buymeacoffee.com; connect-src 'self' https://challenges.cloudflare.com https://api.buymeacoffee.com; frame-src 'self' https://*.buymeacoffee.com; child-src 'self' https://*.buymeacoffee.com; object-src 'none'"
    response.headers['Permissions-Policy'] = "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
    return response

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

from utils.noticias import get_noticias, atualizar_noticias, limpar_cache_antigo
from utils.ine import get_inflacao
from utils.carros import calcular_isv, calcular_iuc
from utils.pdf import gerar_pdf_resultado
from utils.subsidio import calcular_subsidio
from utils.credito import calcular_credito, calcular_tabela_amortizacao
from utils.salario import calcular_salario
from utils.rescisao import calcular_rescisao
from utils.poupanca import calcular_poupanca
from rate_limits import limiter
from security_logger import log_security_event, log_brute_force_attempt, log_invalid_input
from ip_blocker import check_ip_block, register_failed_attempt, is_blocked, get_block_reason

DATABASE = "database.db"

def validar_numero(valor, nome="valor", min_val=0, max_val=1000000):
    try:
        num = float(valor)
        if num < min_val or num > max_val:
            return None, f"{nome} deve estar entre {min_val} e {max_val}"
        return num, None
    except (ValueError, TypeError):
        return None, f"{nome} inválido"

def validar_data(data_str, nome="data"):
    if not data_str:
        return None, f"{nome} obrigatória"
    try:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
        if data_obj.year < 1900 or data_obj.year > 2100:
            return None, f"{nome} com ano inválido"
        return data_str, None
    except ValueError:
        return None, f"{nome} no formato inválido (deve ser AAAA-MM-DD)"

def init_db_if_missing():
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
            print(f"[AVISO] Não foi possível atualizar notícias: {e}")
        print("[OK] Base de dados criada com sucesso")

init_db_if_missing()

def get_db():
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con

def guardar_historico(tipo, inputs_dict, resultado_dict):
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
# ROTAS HTML
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
            "poupanca": "Poupança",
            "isv": "ISV",
            "iuc": "IUC",
            "inflacao": "Inflação",
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
@check_ip_block()
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
            register_failed_attempt(request.remote_addr, request.form.get("bruto", ""), "/salario")
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
                log_invalid_input(request.remote_addr, "/salario", request.form.get("subsidio_alimentacao", ""))
                register_failed_attempt(request.remote_addr, request.form.get("bruto", ""), "/salario")
                return render_template("salario.html", erro=erro, regime=regime, bruto=bruto)
            estado_civil = request.form.get("estado_civil", "solteiro")
            resultado = calcular_salario(
                bruto=bruto,
                regime="outrem",
                subsidio_alimentacao=subsidio_alimentacao,
                estado_civil=estado_civil
            )
        else:
            coeficiente_atividade, erro = validar_numero(request.form.get("coeficiente_atividade", 0.75), "Coeficiente de atividade", 0, 1)
            if erro:
                log_invalid_input(request.remote_addr, "/salario", request.form.get("coeficiente_atividade", ""))
                register_failed_attempt(request.remote_addr, request.form.get("bruto", ""), "/salario")
                return render_template("salario.html", erro=erro, regime=regime, bruto=bruto)
            retencao_irs, erro = validar_numero(request.form.get("retencao_irs", 0.15), "Retenção IRS", 0, 1)
            if erro:
                log_invalid_input(request.remote_addr, "/salario", request.form.get("retencao_irs", ""))
                register_failed_attempt(request.remote_addr, request.form.get("bruto", ""), "/salario")
                return render_template("salario.html", erro=erro, regime=regime, bruto=bruto)
            isento_ss = request.form.get("isento_ss", "nao")
            resultado = calcular_salario(
                bruto=bruto,
                regime="eni",
                coeficiente_atividade=coeficiente_atividade,
                retencao_irs=retencao_irs,
                isento_ss=isento_ss
            )

        log_security_event("CALCULO_SALARIO", request.remote_addr, f"Bruto: {bruto}")
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
@check_ip_block()
@limiter.limit("5 per minute")
def credito():
    resultado = None
    tabela = None
    erro = None
    
    valor_imovel = 200000
    entrada = 20000
    prazo_anos = 30
    spread = 1.0
    euribor = 3.5

    if request.method == "POST":
        val_imovel_raw = request.form.get("valor_imovel", "0")
        entrada_raw = request.form.get("entrada", "0")
        prazo_raw = request.form.get("prazo_anos", "30")
        spread_raw = request.form.get("spread", "0")
        euribor_raw = request.form.get("euribor", "0")

        valor_imovel, erro = validar_numero(val_imovel_raw, "Valor do imóvel")
        if erro:
            log_invalid_input(request.remote_addr, "/credito", val_imovel_raw)
            register_failed_attempt(request.remote_addr, val_imovel_raw, "/credito")
            return render_template("credito.html", erro=erro, valor_imovel=val_imovel_raw, entrada=entrada_raw, prazo_anos=prazo_raw, spread=spread_raw, euribor=euribor_raw)
            
        entrada, erro = validar_numero(entrada_raw, "Entrada")
        if erro:
            log_invalid_input(request.remote_addr, "/credito", entrada_raw)
            register_failed_attempt(request.remote_addr, entrada_raw, "/credito")
            return render_template("credito.html", erro=erro, valor_imovel=valor_imovel, entrada=entrada_raw, prazo_anos=prazo_raw, spread=spread_raw, euribor=euribor_raw)
            
        prazo_anos, erro = validar_numero(prazo_raw, "Prazo", 1, 50)
        if erro:
            log_invalid_input(request.remote_addr, "/credito", prazo_raw)
            register_failed_attempt(request.remote_addr, prazo_raw, "/credito")
            return render_template("credito.html", erro=erro, valor_imovel=valor_imovel, entrada=entrada, prazo_anos=prazo_raw, spread=spread_raw, euribor=euribor_raw)
        prazo_anos = int(prazo_anos)
        
        spread, erro = validar_numero(spread_raw, "Spread", 0, 100)
        if erro:
            log_invalid_input(request.remote_addr, "/credito", spread_raw)
            register_failed_attempt(request.remote_addr, spread_raw, "/credito")
            return render_template("credito.html", erro=erro, valor_imovel=valor_imovel, entrada=entrada, prazo_anos=prazo_anos, spread=spread_raw, euribor=euribor_raw)
            
        euribor, erro = validar_numero(euribor_raw, "Euribor", -100, 100)
        if erro:
            log_invalid_input(request.remote_addr, "/credito", euribor_raw)
            register_failed_attempt(request.remote_addr, euribor_raw, "/credito")
            return render_template("credito.html", erro=erro, valor_imovel=valor_imovel, entrada=entrada, prazo_anos=prazo_anos, spread=spread, euribor=euribor_raw)

        resultado = calcular_credito(valor_imovel, entrada, prazo_anos, spread, euribor)
        tabela = calcular_tabela_amortizacao(valor_imovel, entrada, prazo_anos, spread, euribor, limite=12)

        log_security_event("CALCULO_CREDITO", request.remote_addr, f"Valor: {valor_imovel}")
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

    return render_template("credito.html", 
                           resultado=resultado, 
                           tabela=tabela, 
                           erro=erro, 
                           valor_imovel=valor_imovel, 
                           entrada=entrada, 
                           prazo_anos=prazo_anos, 
                           spread=spread, 
                           euribor=euribor)

@app.route("/rescisao", methods=["GET", "POST"])
@check_ip_block()
@limiter.limit("5 per minute")
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
            log_invalid_input(request.remote_addr, "/rescisao", request.form.get("vencimento_base", ""))
            register_failed_attempt(request.remote_addr, request.form.get("vencimento_base", ""), "/rescisao")
            return render_template("rescisao.html", erro=erro)
            
        subsidio_alimentacao, erro = validar_numero(request.form.get("subsidio_alimentacao", 0), "Subsídio alimentação")
        if erro:
            log_invalid_input(request.remote_addr, "/rescisao", request.form.get("subsidio_alimentacao", ""))
            register_failed_attempt(request.remote_addr, request.form.get("subsidio_alimentacao", ""), "/rescisao")
            return render_template("rescisao.html", erro=erro)
            
        data_inicio, erro = validar_data(request.form.get("data_inicio", ""), "Data de início")
        if erro:
            log_invalid_input(request.remote_addr, "/rescisao", request.form.get("data_inicio", ""))
            register_failed_attempt(request.remote_addr, request.form.get("data_inicio", ""), "/rescisao")
            return render_template("rescisao.html", erro=erro)

        data_fim, erro = validar_data(request.form.get("data_fim", ""), "Data de fim")
        if erro:
            log_invalid_input(request.remote_addr, "/rescisao", request.form.get("data_fim", ""))
            register_failed_attempt(request.remote_addr, request.form.get("data_fim", ""), "/rescisao")
            return render_template("rescisao.html", erro=erro)

        if data_inicio and data_fim:
            d_ini = datetime.strptime(data_inicio, "%Y-%m-%d")
            d_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            if d_fim < d_ini:
                erro = "A data de fim não pode ser anterior à data de início"
                log_invalid_input(request.remote_addr, "/rescisao", f"{data_inicio} > {data_fim}")
                register_failed_attempt(request.remote_addr, data_fim, "/rescisao")
                return render_template("rescisao.html", erro=erro)

        motivo = request.form.get("motivo", "caducidade_termo")
        meses_layoff, erro = validar_numero(request.form.get("meses_layoff", 0), "Meses em lay-off", 0, 100)
        if erro:
            log_invalid_input(request.remote_addr, "/rescisao", request.form.get("meses_layoff", ""))
            register_failed_attempt(request.remote_addr, request.form.get("meses_layoff", ""), "/rescisao")
            return render_template("rescisao.html", erro=erro)
        meses_layoff = int(meses_layoff)
        
        ferias_vencidas, erro = validar_numero(request.form.get("ferias_vencidas", 0), "Férias vencidas", 0, 1000)
        if erro:
            log_invalid_input(request.remote_addr, "/rescisao", request.form.get("ferias_vencidas", ""))
            register_failed_attempt(request.remote_addr, request.form.get("ferias_vencidas", ""), "/rescisao")
            return render_template("rescisao.html", erro=erro)
        ferias_vencidas = int(ferias_vencidas)
        
        horas_formacao, erro = validar_numero(request.form.get("horas_formacao", 0), "Horas de formação", 0, 1000)
        if erro:
            log_invalid_input(request.remote_addr, "/rescisao", request.form.get("horas_formacao", ""))
            register_failed_attempt(request.remote_addr, request.form.get("horas_formacao", ""), "/rescisao")
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

        log_security_event("CALCULO_RESCISAO", request.remote_addr, f"Vencimento: {vencimento_base}")
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
@check_ip_block()
@limiter.limit("5 per minute")
def subsidio():
    resultado = None
    erro = None
    
    media_salarial = 1000
    idade = 30
    meses_desconto = 24

    if request.method == "POST":
        media_raw = request.form.get("media_salarial", "0")
        idade_raw = request.form.get("idade", "0")
        descontos_raw = request.form.get("meses_desconto", "0")

        media_salarial, erro = validar_numero(media_raw, "Média salarial")
        if erro:
            log_invalid_input(request.remote_addr, "/subsidio", media_raw)
            register_failed_attempt(request.remote_addr, media_raw, "/subsidio")
            return render_template("subsidio.html", erro=erro, media_salarial=media_raw, idade=idade_raw, meses_desconto=descontos_raw)
            
        idade, erro = validar_numero(idade_raw, "Idade", 16, 100)
        if erro:
            log_invalid_input(request.remote_addr, "/subsidio", idade_raw)
            register_failed_attempt(request.remote_addr, idade_raw, "/subsidio")
            return render_template("subsidio.html", erro=erro, media_salarial=media_salarial, idade=idade_raw, meses_desconto=descontos_raw)
        idade = int(idade)
        
        meses_desconto, erro = validar_numero(descontos_raw, "Meses de desconto", 0, 999)
        if erro:
            log_invalid_input(request.remote_addr, "/subsidio", descontos_raw)
            register_failed_attempt(request.remote_addr, descontos_raw, "/subsidio")
            return render_template("subsidio.html", erro=erro, media_salarial=media_salarial, idade=idade, meses_desconto=descontos_raw)
        meses_desconto = int(meses_desconto)

        resultado = calcular_subsidio(media_salarial, idade, meses_desconto)

        log_security_event("CALCULO_SUBSIDIO", request.remote_addr, f"Média: {media_salarial}")
        guardar_historico(
            tipo="subsidio",
            inputs_dict={
                "media_salarial": media_salarial,
                "idade": idade,
                "meses_desconto": meses_desconto
            },
            resultado_dict=resultado
        )

    return render_template("subsidio.html", 
                           resultado=resultado, 
                           erro=erro, 
                           media_salarial=media_salarial, 
                           idade=idade, 
                           meses_desconto=meses_desconto)

# =============================================================================
# ROTAS DA API
# =============================================================================

@app.route("/api/salario", methods=["POST"])
@limiter.limit("10 per minute")
@check_ip_block()
def api_salario():
    try:
        dados = request.get_json()
        if not dados or "bruto" not in dados:
            return jsonify({"erro": "Dados inválidos. O campo 'bruto' é obrigatório."}), 400
        
        bruto, erro = validar_numero(dados["bruto"], "bruto")
        if erro:
            return jsonify({"erro": erro}), 400

        if dados.get("regime") == "eni":
            coef, erro = validar_numero(dados.get("coeficiente_atividade", 0.75), "coeficiente_atividade", 0, 1)
            if erro: return jsonify({"erro": erro}), 400
            ret, erro = validar_numero(dados.get("retencao_irs", 0.15), "retencao_irs", 0, 1)
            if erro: return jsonify({"erro": erro}), 400

            resultado = calcular_salario(
                bruto=bruto,
                regime="eni",
                coeficiente_atividade=coef,
                retencao_irs=ret,
                isento_ss=dados.get("isento_ss", "nao")
            )
        else:
            sub_alim, erro = validar_numero(dados.get("subsidio_alimentacao", 6.0), "subsidio_alimentacao")
            if erro: return jsonify({"erro": erro}), 400

            resultado = calcular_salario(
                bruto=bruto,
                regime="outrem",
                subsidio_alimentacao=sub_alim,
                estado_civil=dados.get("estado_civil", "solteiro")
            )
        log_security_event("API_SALARIO", request.remote_addr, f"Bruto: {bruto}")
        guardar_historico(tipo="salario", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        return jsonify({"erro": "Erro interno no servidor."}), 500

@app.route("/api/credito", methods=["POST"])
@check_ip_block()
def api_credito():
    try:
        dados = request.get_json()
        if not dados or "valor_imovel" not in dados:
            return jsonify({"erro": "Dados inválidos. O campo 'valor_imovel' é obrigatório."}), 400
        
        valor_imovel, erro = validar_numero(dados["valor_imovel"], "valor_imovel")
        if erro: return jsonify({"erro": erro}), 400
        entrada, erro = validar_numero(dados.get("entrada", 0), "entrada")
        if erro: return jsonify({"erro": erro}), 400
        prazo_anos, erro = validar_numero(dados.get("prazo_anos", 30), "prazo_anos", 1, 50)
        if erro: return jsonify({"erro": erro}), 400
        spread, erro = validar_numero(dados.get("spread", 1.0), "spread", 0, 100)
        if erro: return jsonify({"erro": erro}), 400
        euribor, erro = validar_numero(dados.get("euribor", 3.5), "euribor", -100, 100)
        if erro: return jsonify({"erro": erro}), 400

        resultado = calcular_credito(valor_imovel, entrada, int(prazo_anos), spread, euribor)
        log_security_event("API_CREDITO", request.remote_addr, f"Valor: {valor_imovel}")
        guardar_historico(tipo="credito", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        return jsonify({"erro": "Erro interno no servidor."}), 500

@app.route("/api/rescisao", methods=["POST"])
@check_ip_block()
def api_rescisao():
    try:
        dados = request.get_json()
        if not dados or "vencimento_base" not in dados:
            return jsonify({"erro": "Dados inválidos. O campo 'vencimento_base' é obrigatório."}), 400
        
        vencimento_base, erro = validar_numero(dados["vencimento_base"], "vencimento_base")
        if erro: return jsonify({"erro": erro}), 400
        subsidio_alimentacao, erro = validar_numero(dados.get("subsidio_alimentacao", 6.0), "subsidio_alimentacao")
        if erro: return jsonify({"erro": erro}), 400
        
        data_inicio, erro = validar_data(dados.get("data_inicio", "2020-01-01"), "data_inicio")
        if erro: return jsonify({"erro": erro}), 400
        data_fim, erro = validar_data(dados.get("data_fim", "2026-01-01"), "data_fim")
        if erro: return jsonify({"erro": erro}), 400

        meses_layoff, erro = validar_numero(dados.get("meses_layoff", 0), "meses_layoff", 0, 100)
        if erro: return jsonify({"erro": erro}), 400
        ferias_vencidas, erro = validar_numero(dados.get("ferias_vencidas", 0), "ferias_vencidas", 0, 1000)
        if erro: return jsonify({"erro": erro}), 400
        horas_formacao, erro = validar_numero(dados.get("horas_formacao", 0), "horas_formacao", 0, 1000)
        if erro: return jsonify({"erro": erro}), 400

        resultado = calcular_rescisao(
            vencimento_base=vencimento_base,
            subsidio_alimentacao=subsidio_alimentacao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            motivo=dados.get("motivo", "caducidade_termo"),
            meses_layoff=int(meses_layoff),
            ferias_vencidas=int(ferias_vencidas),
            horas_formacao=int(horas_formacao)
        )
        log_security_event("API_RESCISAO", request.remote_addr, f"Vencimento: {vencimento_base}")
        guardar_historico(tipo="rescisao", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        return jsonify({"erro": "Erro interno no servidor."}), 500

@app.route("/api/subsidio", methods=["POST"])
@check_ip_block()
def api_subsidio():
    try:
        dados = request.get_json()
        if not dados or "media_salarial" not in dados:
            return jsonify({"erro": "Dados inválidos. O campo 'media_salarial' é obrigatório."}), 400
        
        media_salarial, erro = validar_numero(dados["media_salarial"], "media_salarial")
        if erro: return jsonify({"erro": erro}), 400
        idade, erro = validar_numero(dados.get("idade", 30), "idade", 16, 100)
        if erro: return jsonify({"erro": erro}), 400
        meses_desconto, erro = validar_numero(dados.get("meses_desconto", 12), "meses_desconto", 0, 999)
        if erro: return jsonify({"erro": erro}), 400

        resultado = calcular_subsidio(media_salarial, int(idade), int(meses_desconto))
        log_security_event("API_SUBSIDIO", request.remote_addr, f"Média: {media_salarial}")
        guardar_historico(tipo="subsidio", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        log_security_event("API_ERROR", request.remote_addr, str(e))
        return jsonify({"erro": "Erro interno no servidor."}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "API Calculadoras Portugal 2026"})

# =============================================================================
# ROTAS API - INE E CARROS
# =============================================================================

@app.route("/api/ine/inflacao", methods=["GET"])
def api_ine_inflacao():
    try:
        resultado = get_inflacao()
        if "erro" in resultado:
            return jsonify(resultado), 500
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/carros/isv", methods=["GET"])
def api_carros_isv():
    try:
        co2 = request.args.get('co2', type=int)
        cilindrada = request.args.get('cilindrada', type=int)
        ano = request.args.get('ano', type=int)
        
        if co2 is None or cilindrada is None or ano is None:
            return jsonify({"erro": "Parâmetros obrigatórios: co2, cilindrada, ano"}), 400
        
        resultado = calcular_isv(co2, cilindrada, ano)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/carros/iuc", methods=["GET"])
def api_carros_iuc():
    try:
        co2 = request.args.get("co2", type=int)
        cilindrada = request.args.get("cilindrada", type=int)
        ano = request.args.get("ano", type=int)
        combustivel = request.args.get("combustivel", type=str, default="gasolina")
        
        if co2 is None or cilindrada is None or ano is None:
            return jsonify({"erro": "Parâmetros obrigatórios: co2, cilindrada, ano"}), 400
        
        resultado = calcular_iuc(co2, cilindrada, ano, combustivel)
        
        if "erro" in resultado:
            return jsonify(resultado), 400
            
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
        
# =============================================================================
# ROTAS PDF
# =============================================================================

@app.route("/salario/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def salario_pdf():
    try:
        bruto = request.args.get("salario_bruto", type=float)
        regime = request.args.get("regime", "outrem")
        
        if not bruto:
            return jsonify({"erro": "Parâmetro salario_bruto obrigatório"}), 400
        
        if regime == "eni":
            resultado = calcular_salario(bruto=bruto, regime="eni", coeficiente_atividade=0.75, retencao_irs=0.15, isento_ss="nao")
            inputs = {"Salário Bruto": f"€{bruto:.2f}", "Regime": "Trabalhador Independente (ENI)"}
        else:
            resultado = calcular_salario(bruto=bruto, regime="outrem", subsidio_alimentacao=6.0, estado_civil="solteiro")
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
        return jsonify({"erro": str(e)}), 500

@app.route("/credito/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def credito_pdf():
    try:
        valor_imovel = request.args.get("valor_imovel", type=float)
        entrada = request.args.get("entrada", type=float, default=0)
        prazo_anos = request.args.get("prazo_anos", type=int, default=30)
        spread = request.args.get("spread", type=float, default=1.5)
        euribor = request.args.get("euribor", type=float, default=3.5)
        
        if not valor_imovel:
            return jsonify({"erro": "Parâmetro valor_imovel obrigatório"}), 400
        
        resultado = calcular_credito(valor_imovel, entrada, prazo_anos, spread, euribor)
        inputs = {"Valor do Imóvel": f"€{valor_imovel:.2f}", "Entrada": f"€{entrada:.2f}", "Prazo": f"{prazo_anos} anos", "Spread": f"{spread}%", "Euribor": f"{euribor}%"}
        
        pdf = gerar_pdf_resultado("Crédito Habitação", inputs, resultado)
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=credito_{valor_imovel:.0f}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/rescisao/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def rescisao_pdf():
    try:
        vencimento_base = request.args.get("vencimento_base", type=float)
        subsidio_alimentacao = request.args.get("subsidio_alimentacao", type=float, default=6.0)
        data_inicio = request.args.get("data_inicio", "2020-01-15")
        data_fim = request.args.get("data_fim", "2026-07-16")
        motivo = request.args.get("motivo", "caducidade_termo")
        
        if not vencimento_base:
            return jsonify({"erro": "Parâmetro vencimento_base obrigatório"}), 400
        
        resultado = calcular_rescisao(vencimento_base, subsidio_alimentacao, data_inicio, data_fim, motivo)
        inputs = {"Vencimento Base": f"€{vencimento_base:.2f}", "Subsídio Alimentação": f"€{subsidio_alimentacao:.2f}/dia", "Data Início": data_inicio, "Data Fim": data_fim, "Motivo": motivo}
        
        pdf = gerar_pdf_resultado("Rescisão de Contrato", inputs, resultado)
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=rescisao_{vencimento_base:.0f}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/subsidio/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def subsidio_pdf():
    try:
        media_salarial = request.args.get("media_salarial", type=float)
        idade = request.args.get("idade", type=int, default=30)
        meses_desconto = request.args.get("meses_desconto", type=int, default=12)
        
        if not media_salarial:
            return jsonify({"erro": "Parâmetro media_salarial obrigatório"}), 400
        
        resultado = calcular_subsidio(media_salarial, idade, meses_desconto)
        inputs = {"Média Salarial": f"€{media_salarial:.2f}", "Idade": f"{idade} anos", "Meses de Desconto": f"{meses_desconto} meses"}
        
        pdf = gerar_pdf_resultado("Subsídio de Desemprego", inputs, resultado)
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=subsidio_{media_salarial:.0f}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/iuc/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def iuc_pdf():
    try:
        ano = request.args.get("ano", type=int)
        cilindrada = request.args.get("cilindrada", type=int)
        co2 = request.args.get("co2", type=int)
        combustivel = request.args.get("combustivel", type=str, default="gasolina")

        if not ano or not cilindrada or co2 is None:
            return jsonify({"erro": "Parâmetros obrigatórios em falta: ano, cilindrada, co2"}), 400

        resultado = calcular_iuc(co2, cilindrada, ano, combustivel)
        inputs = {
            "Ano do Veículo": str(ano),
            "Cilindrada": f"{cilindrada} cc",
            "Emissões CO₂": f"{co2} g/km",
            "Combustível": combustivel.capitalize()
        }

        pdf = gerar_pdf_resultado("Imposto Único de Circulação (IUC)", inputs, resultado)
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=iuc_{ano}_{cilindrada}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# =============================================================================
# TRATEMENTO DE ERROS
# =============================================================================
@app.errorhandler(Exception)
def handle_exception(e):
    log_security_event("INTERNAL_SERVER_ERROR", request.remote_addr, str(e))
    return render_template("500.html"), 500

@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Página não encontrada</h1><p><a href='/'>Voltar ao início</a></p>", 404

# =============================================================================
# ROTAS PARA AS NOVAS CALCULADORAS
# =============================================================================

@app.route("/inflacao", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@check_ip_block()
def inflacao():
    erro = None
    resultado = None

    if request.method == "POST":
        try:
            resultado = get_inflacao()
            if "erro" in resultado:
                erro = resultado["erro"]
                resultado = None
            else:
                log_security_event("CALCULO_INFLACAO", request.remote_addr, "Consulta inflação")
                guardar_historico(tipo="inflacao", inputs_dict={}, resultado_dict=resultado)
        except Exception as e:
            erro = str(e)

    return render_template("inflacao.html", resultado=resultado, erro=erro)

@app.route("/isv", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@check_ip_block()
def isv():
    erro = None
    resultado = None
    ano = 2020
    cilindrada = 2000
    co2 = 150

    if request.method == "POST":
        try:
            ano = int(request.form.get("ano", 2020))
            cilindrada = float(request.form.get("cilindrada", 2000))
            co2 = float(request.form.get("co2", 150))

            if ano < 1990 or ano > 2026:
                erro = "Ano deve estar entre 1990 e 2026"
            elif cilindrada <= 0:
                erro = "Cilindrada deve ser positiva"
            elif co2 < 0:
                erro = "CO₂ deve ser positivo"

            if not erro:
                res_isv = calcular_isv(co2, cilindrada, ano)
                if "erro" in res_isv:
                    erro = res_isv["erro"]
                else:
                    resultado = {"isv": res_isv}
                    log_security_event("CALCULO_ISV", request.remote_addr, f"Ano:{ano} CC:{cilindrada} CO2:{co2}")
                    guardar_historico(
                        tipo="isv",
                        inputs_dict={"ano": ano, "cilindrada": cilindrada, "co2": co2},
                        resultado_dict=resultado
                    )
        except ValueError:
            erro = "Valores inválidos. Por favor, insira números."
        except Exception as e:
            erro = str(e)

    return render_template("isv.html", resultado=resultado, erro=erro, ano=ano, cilindrada=cilindrada, co2=co2)

@app.route("/iuc", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@check_ip_block()
def iuc():
    erro = None
    resultado = None
    ano = 2020
    co2 = 150
    cilindrada = 1500
    combustivel = "gasolina"

    if request.method == "POST":
        try:
            ano = int(request.form.get("ano", 2020))
            co2 = int(request.form.get("co2", 150))
            cilindrada = int(request.form.get("cilindrada", 1500))
            combustivel = request.form.get("combustivel", "gasolina")

            if ano < 1990 or ano > 2026:
                erro = "Ano deve estar entre 1990 e 2026"
            elif co2 < 0:
                erro = "CO₂ deve ser positivo"
            elif cilindrada <= 0:
                erro = "Cilindrada deve ser positiva"

            if not erro:
                resultado = calcular_iuc(co2, cilindrada, ano, combustivel)
                if "erro" in resultado:
                    erro = resultado["erro"]
                    resultado = None
                else:
                    log_security_event("CALCULO_IUC", request.remote_addr, f"Ano:{ano} CO2:{co2} CC:{cilindrada} Combustivel:{combustivel}")
                    guardar_historico(
                        tipo="iuc",
                        inputs_dict={"ano": ano, "co2": co2, "cilindrada": cilindrada, "combustivel": combustivel},
                        resultado_dict=resultado
                    )
        except ValueError:
            erro = "Valores inválidos. Por favor, insira números."
        except Exception as e:
            erro = str(e)

    return render_template("iuc.html", resultado=resultado, erro=erro, ano=ano, co2=co2, cilindrada=cilindrada, combustivel=combustivel)

# =============================================================================
# ROTA - SIMULADOR DE POUPANÇA
# =============================================================================

@app.route("/poupanca", methods=["GET", "POST"])
@limiter.limit("5 per minute")
@check_ip_block()
def poupanca():
    erro = None
    resultado = None
    capital_inicial = 1000
    contribuicao_mensal = 100
    taxa_juro = 5
    periodo = 10

    if request.method == "POST":
        try:
            capital_inicial = float(request.form.get("capital_inicial", 1000))
            contribuicao_mensal = float(request.form.get("contribuicao_mensal", 0))
            taxa_juro = float(request.form.get("taxa_juro", 5))
            periodo = int(request.form.get("periodo", 10))

            if capital_inicial < 0:
                erro = "Capital inicial deve ser positivo"
            elif contribuicao_mensal < 0:
                erro = "Contribuição mensal deve ser positiva"
            elif taxa_juro < 0:
                erro = "Taxa de juro deve ser positiva"
            elif periodo < 1:
                erro = "Período deve ser pelo menos 1 ano"

            if not erro:
                resultado = calcular_poupanca(capital_inicial, contribuicao_mensal, taxa_juro, periodo)
                log_security_event("CALCULO_POUPANCA", request.remote_addr, f"Capital:{capital_inicial} Juro:{taxa_juro} Anos:{periodo}")
                guardar_historico(
                    tipo="poupanca",
                    inputs_dict={
                        "capital_inicial": capital_inicial,
                        "contribuicao_mensal": contribuicao_mensal,
                        "taxa_juro": taxa_juro,
                        "periodo": periodo
                    },
                    resultado_dict=resultado
                )
        except ValueError:
            erro = "Valores inválidos. Por favor, insira números."
        except Exception as e:
            erro = str(e)

    return render_template("poupanca.html",
                          resultado=resultado,
                          erro=erro,
                          capital_inicial=capital_inicial,
                          contribuicao_mensal=contribuicao_mensal,
                          taxa_juro=taxa_juro,
                          periodo=periodo)

@app.route("/poupanca/pdf", methods=["GET"])
@limiter.limit("5 per minute")
def poupanca_pdf():
    try:
        capital_inicial = request.args.get("capital_inicial", type=float)
        contribuicao_mensal = request.args.get("contribuicao_mensal", type=float, default=0)
        taxa_juro = request.args.get("taxa_juro", type=float)
        periodo = request.args.get("periodo", type=int)

        if not capital_inicial or not taxa_juro or not periodo:
            return jsonify({"erro": "Parâmetros obrigatórios: capital_inicial, taxa_juro, periodo"}), 400

        resultado = calcular_poupanca(capital_inicial, contribuicao_mensal, taxa_juro, periodo)
        inputs = {
            "Capital Inicial": f"€{capital_inicial:.2f}",
            "Contribuição Mensal": f"€{contribuicao_mensal:.2f}",
            "Taxa de Juro": f"{taxa_juro}%",
            "Período": f"{periodo} anos"
        }

        pdf = gerar_pdf_resultado("Poupança", inputs, resultado)
        if pdf:
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"attachment; filename=poupanca_{capital_inicial:.0f}.pdf"
            return response
        else:
            return jsonify({"erro": "PDF não disponível", "dados": resultado}), 500
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

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