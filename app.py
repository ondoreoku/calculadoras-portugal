"""
APP.PY — Aplicação Flask Principal (Versão Híbrida: HTML + API + Postgres)
"""
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

# Importa as funções dos módulos de calculadoras e o novo db
from utils.db import get_connection, get_cursor
from utils.noticias import get_noticias, atualizar_noticias, limpar_cache_antigo
from utils.subsidio import calcular_subsidio
from utils.credito import calcular_credito, calcular_tabela_amortizacao
from utils.salario import calcular_salario
from utils.rescisao import calcular_rescisao

# Inicialização automática da DB
def init_db_if_missing():
    """Cria a base de dados e tabelas se não existirem."""
    from initdb import create_tables, seed_taxas
    create_tables()
    seed_taxas()
    print("[INFO] A buscar notícias do RSS...")
    try:
        atualizar_noticias()
        limpar_cache_antigo()
    except Exception as e:
        print(f"[AVISO] Erro ao atualizar notícias: {e}")

init_db_if_missing()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

def guardar_historico(tipo, inputs_dict, resultado_dict):
    """Guarda um cálculo no histórico (funciona em SQLite e Postgres)."""
    try:
        conn, eh_postgres = get_connection()
        cur = get_cursor(conn, eh_postgres)
        
        input_json = json.dumps(inputs_dict, ensure_ascii=False)
        resultado_json = json.dumps(resultado_dict, ensure_ascii=False)
        
        if eh_postgres:
            cur.execute("INSERT INTO historico_calculos (tipo, input_json, resultado_json) VALUES (%s, %s, %s)", (tipo, input_json, resultado_json))
        else:
            cur.execute("INSERT INTO historico_calculos (tipo, input_json, resultado_json) VALUES (?, ?, ?)", (tipo, input_json, resultado_json))
            
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[ERRO] Ao guardar histórico: {e}")

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
        atualizar_noticias()
        limpar_cache_antigo()
    except Exception as e:
        print(f"[ERRO] Falha na atualização: {e}")
    return redirect(url_for("home"))

@app.route("/historico")
def historico():
    conn, eh_postgres = get_connection()
    cur = get_cursor(conn, eh_postgres)
    
    if eh_postgres:
        cur.execute("SELECT tipo, input_json, resultado_json, data_hora FROM historico_calculos ORDER BY data_hora DESC LIMIT 50")
    else:
        cur.execute("SELECT tipo, input_json, resultado_json, data_hora FROM historico_calculos ORDER BY data_hora DESC LIMIT 50")
        
    rows = cur.fetchall()
    cur.close()
    conn.close()

    registos = []
    for row in rows:
        inputs = json.loads(row["input_json"]) if row["input_json"] else {}
        resultado = json.loads(row["resultado_json"]) if row["resultado_json"] else {}
        registos.append({
            "tipo": {"subsidio": "Subsídio", "salario": "Salário", "credito": "Crédito", "rescisao": "Rescisão"}.get(row["tipo"], row["tipo"]),
            "inputs": inputs, "resultado": resultado, "data_hora": row["data_hora"],
        })
    return render_template("historico.html", registos=registos)

@app.route("/salario", methods=["GET", "POST"])
def salario_page():
    resultado = None
    # ... (mantém a tua lógica de GET/POST e render_template exatamente como tinhas) ...
    # Para poupar espaço, assume que a lógica de processamento do form é a mesma.
    # Apenas muda a chamada para guardar_historico (que já está atualizada acima).
    if request.method == "POST":
        regime = request.form.get("regime", "outrem")
        bruto = float(request.form.get("bruto", 0))
        if regime == "outrem":
            resultado = calcular_salario(bruto=bruto, regime="outrem", subsidio_alimentacao=float(request.form.get("subsidio_alimentacao", 0)), estado_civil=request.form.get("estado_civil", "solteiro"))
        else:
            resultado = calcular_salario(bruto=bruto, regime="eni", coeficiente_atividade=float(request.form.get("coeficiente_atividade", 0.75)), retencao_irs=float(request.form.get("retencao_irs", 0.15)), isento_ss=request.form.get("isento_ss", "nao"))
        guardar_historico(tipo="salario", inputs_dict=request.form.to_dict(), resultado_dict=resultado)
    return render_template("salario.html", resultado=resultado)

@app.route("/credito", methods=["GET", "POST"])
def credito_page():
    resultado = None
    tabela = None
    if request.method == "POST":
        valor_imovel = float(request.form.get("valor_imovel", 0))
        entrada = float(request.form.get("entrada", 0))
        prazo_anos = int(request.form.get("prazo_anos", 0))
        spread = float(request.form.get("spread", 0))
        euribor = float(request.form.get("euribor", 0))
        resultado = calcular_credito(valor_imovel, entrada, prazo_anos, spread, euribor)
        tabela = calcular_tabela_amortizacao(valor_imovel, entrada, prazo_anos, spread, euribor, limite=12)
        guardar_historico(tipo="credito", inputs_dict=request.form.to_dict(), resultado_dict=resultado)
    return render_template("credito.html", resultado=resultado, tabela=tabela)

@app.route("/rescisao", methods=["GET", "POST"])
def rescisao_page():
    resultado = None
    if request.method == "POST":
        resultado = calcular_rescisao(
            vencimento_base=float(request.form.get("vencimento_base", 0)),
            subsidio_alimentacao=float(request.form.get("subsidio_alimentacao", 0)),
            data_inicio=request.form.get("data_inicio", ""),
            data_fim=request.form.get("data_fim", ""),
            motivo=request.form.get("motivo", "caducidade_termo"),
            meses_layoff=int(request.form.get("meses_layoff", 0)),
            ferias_vencidas=int(request.form.get("ferias_vencidas", 0)),
            horas_formacao=int(request.form.get("horas_formacao", 0))
        )
        guardar_historico(tipo="rescisao", inputs_dict=request.form.to_dict(), resultado_dict=resultado)
    return render_template("rescisao.html", resultado=resultado)

@app.route("/subsidio", methods=["GET", "POST"])
def subsidio_page():
    resultado = None
    if request.method == "POST":
        resultado = calcular_subsidio(float(request.form["media_salarial"]), int(request.form["idade"]), int(request.form["meses_desconto"]))
        guardar_historico(tipo="subsidio", inputs_dict=request.form.to_dict(), resultado_dict=resultado)
    return render_template("subsidio.html", resultado=resultado)

# =============================================================================
# ROTAS API
# =============================================================================
@app.route("/api/salario", methods=["POST"])
def api_salario():
    try:
        dados = request.get_json()
        if not dados or "bruto" not in dados: return jsonify({"erro": "Dados inválidos."}), 400
        if dados.get("regime") == "eni":
            resultado = calcular_salario(bruto=dados["bruto"], regime="eni", coeficiente_atividade=dados.get("coeficiente_atividade", 0.75), retencao_irs=dados.get("retencao_irs", 0.15), isento_ss=dados.get("isento_ss", "nao"))
        else:
            resultado = calcular_salario(bruto=dados["bruto"], regime="outrem", subsidio_alimentacao=dados.get("subsidio_alimentacao", 6.0), estado_civil=dados.get("estado_civil", "solteiro"))
        guardar_historico(tipo="salario", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/rescisao", methods=["POST"])
def api_rescisao():
    try:
        dados = request.get_json()
        if not dados or "vencimento_base" not in dados: return jsonify({"erro": "Dados inválidos."}), 400
        resultado = calcular_rescisao(vencimento_base=dados["vencimento_base"], subsidio_alimentacao=dados.get("subsidio_alimentacao", 6.0), data_inicio=dados.get("data_inicio", "2020-01-01"), data_fim=dados.get("data_fim", "2026-01-01"), motivo=dados.get("motivo", "caducidade_termo"), meses_layoff=int(dados.get("meses_layoff", 0)), ferias_vencidas=int(dados.get("ferias_vencidas", 0)), horas_formacao=int(dados.get("horas_formacao", 0)))
        guardar_historico(tipo="rescisao", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/credito", methods=["POST"])
def api_credito():
    try:
        dados = request.get_json()
        if not dados or "valor_imovel" not in dados: return jsonify({"erro": "Dados inválidos."}), 400
        resultado = calcular_credito(dados["valor_imovel"], dados.get("entrada", 0), dados.get("prazo_anos", 30), dados.get("spread", 1.0), dados.get("euribor", 3.5))
        guardar_historico(tipo="credito", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/subsidio", methods=["POST"])
def api_subsidio():
    try:
        dados = request.get_json()
        if not dados or "media_salarial" not in dados: return jsonify({"erro": "Dados inválidos."}), 400
        resultado = calcular_subsidio(dados["media_salarial"], int(dados.get("idade", 30)), int(dados.get("meses_desconto", 12)))
        guardar_historico(tipo="subsidio", inputs_dict=dados, resultado_dict=resultado)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "API Calculadoras Portugal 2026 (Postgres Ready)!"})

if __name__ == "__main__":
    print("=" * 60)
    print("  Calculadoras Portugal 2026 (Modo Híbrido: HTML + API + Postgres)")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)