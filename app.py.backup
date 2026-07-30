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

DEPENDÊNCIAS:
    — Flask: pip install flask
    — feedparser: pip install feedparser (para notícias RSS)

COMO INICIAR:
    1. python3 initdb.py    (cria a base de dados — só uma vez)
    2. python3 app.py       (inicia o servidor)
    3. Abrir http://127.0.0.1:5000 no browser
================================================================================
"""

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json
from datetime import datetime

# Importa as funções dos módulos de calculadoras
from utils.noticias import get_noticias, atualizar_noticias, limpar_cache_antigo
from utils.subsidio import calcular_subsidio
from utils.credito import calcular_credito, calcular_tabela_amortizacao
from utils.salario import calcular_salario
from utils.rescisao import calcular_rescisao

DATABASE = "database.db"


# =============================================================================
# INICIALIZACAO AUTOMATICA DA BASE DE DADOS
# =============================================================================
# No Render (producao), o database.db nao sobe pelo Git (esta no .gitignore).
# Esta funcao cria a base de dados automaticamente se nao existir.
# =============================================================================
import os

def init_db_if_missing():
    """Cria a base de dados se nao existir (necessario no Render)."""
    if not os.path.exists(DATABASE):
        print("[INFO] Base de dados nao encontrada. A criar...")
        import initdb
        initdb.create_tables()
        initdb.seed_taxas()
        # Busca noticias automaticamente no primeiro arranque
        # Assim o utilizador ve noticias reais desde o primeiro acesso
        print("[INFO] A buscar noticias do RSS...")
        from utils.noticias import atualizar_noticias, limpar_cache_antigo
        try:
            inseridas = atualizar_noticias()
            limpar_cache_antigo()
            print(f"[OK] {inseridas} noticias inseridas automaticamente")
        except Exception as e:
            print(f"[AVISO] Nao foi possivel atualizar noticias: {e}")
        print("[OK] Base de dados criada com sucesso")

# Chama no arranque da aplicacao
init_db_if_missing()

app = Flask(__name__)


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
# ROTA 1: HOME PAGE
# =============================================================================
@app.route("/")
def home():
    noticias = get_noticias(limite=9)
    return render_template("home.html", noticias=noticias)


# =============================================================================
# ROTA 2: ATUALIZAR NOTÍCIAS
# =============================================================================
@app.route("/atualizar_noticias")
def atualizar_noticias_rota():
    try:
        inseridas = atualizar_noticias()
        limpar_cache_antigo()
        print(f"[INFO] Atualização concluída: {inseridas} notícias novas")
    except Exception as e:
        print(f"[ERRO] Falha na atualização: {e}")
    return redirect(url_for("home"))


# =============================================================================
# ROTA 3: HISTÓRICO
# =============================================================================
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


# =============================================================================
# ROTA 4: SALÁRIO LÍQUIDO
# =============================================================================
@app.route("/salario", methods=["GET", "POST"])
def salario():
    resultado = None
    regime = "outrem"
    bruto = 1500
    subsidio_alimentacao = 6.0
    estado_civil = "solteiro"
    coeficiente_atividade = 0.75
    retencao_irs = 0.15
    isento_ss = "nao"

    if request.method == "POST":
        regime = request.form.get("regime", "outrem")
        bruto = float(request.form.get("bruto", 0))

        if regime == "outrem":
            subsidio_alimentacao = float(request.form.get("subsidio_alimentacao", 0))
            estado_civil = request.form.get("estado_civil", "solteiro")
            resultado = calcular_salario(
                bruto=bruto,
                regime="outrem",
                subsidio_alimentacao=subsidio_alimentacao,
                estado_civil=estado_civil
            )
        else:
            coeficiente_atividade = float(request.form.get("coeficiente_atividade", 0.75))
            retencao_irs = float(request.form.get("retencao_irs", 0.15))
            isento_ss = request.form.get("isento_ss", "nao")
            resultado = calcular_salario(
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
                          regime=regime,
                          bruto=bruto,
                          subsidio_alimentacao=subsidio_alimentacao,
                          estado_civil=estado_civil,
                          coeficiente_atividade=coeficiente_atividade,
                          retencao_irs=retencao_irs,
                          isento_ss=isento_ss)


# =============================================================================
# ROTA 5: CRÉDITO HABITAÇÃO
# =============================================================================
@app.route("/credito", methods=["GET", "POST"])
def credito():
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

    return render_template("credito.html", resultado=resultado, tabela=tabela)


# =============================================================================
# ROTA 6: RESCISÃO
# =============================================================================
@app.route("/rescisao", methods=["GET", "POST"])
def rescisao():
    resultado = None
    vencimento_base = 1200
    subsidio_alimentacao = 6.0
    data_inicio = "2020-01-15"
    data_fim = "2026-07-16"
    motivo = "caducidade_termo"
    meses_layoff = 0
    ferias_vencidas = 0
    horas_formacao = 0

    if request.method == "POST":
        vencimento_base = float(request.form.get("vencimento_base", 0))
        subsidio_alimentacao = float(request.form.get("subsidio_alimentacao", 0))
        data_inicio = request.form.get("data_inicio", "")
        data_fim = request.form.get("data_fim", "")
        motivo = request.form.get("motivo", "caducidade_termo")
        meses_layoff = int(request.form.get("meses_layoff", 0))
        ferias_vencidas = int(request.form.get("ferias_vencidas", 0))
        horas_formacao = int(request.form.get("horas_formacao", 0))

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
                          vencimento_base=vencimento_base,
                          subsidio_alimentacao=subsidio_alimentacao,
                          data_inicio=data_inicio,
                          data_fim=data_fim,
                          motivo=motivo,
                          meses_layoff=meses_layoff,
                          ferias_vencidas=ferias_vencidas,
                          horas_formacao=horas_formacao)


# =============================================================================
# ROTA 7: SUBSÍDIO DESEMPREGO (já funcional)
# =============================================================================
@app.route("/subsidio", methods=["GET", "POST"])
def subsidio():
    resultado = None

    if request.method == "POST":
        media_salarial = float(request.form["media_salarial"])
        idade = int(request.form["idade"])
        meses_desconto = int(request.form["meses_desconto"])

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

    return render_template("subsidio.html", resultado=resultado)


# =============================================================================
# INICIALIZAÇÃO DO SERVIDOR
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Calculadoras Portugal 2026")
    print("  Servidor Flask a iniciar...")
    print("=" * 60)
    # Usa PORT do ambiente (necessario para Render/Railway)
    # Se nao existir, usa 5000 (localhost)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
