#!/bin/bash
set -e

echo "=========================================="
echo "🚀 ATUALIZAÇÃO FINAL - CALCULADORAS PORTUGAL"
echo "=========================================="

# ====================================================================
# 1. CRIAR TEMPLATE DA CALCULADORA DE POUPANÇA
# ====================================================================
echo "📄 Criando template poupanca.html..."

cat > templates/poupanca.html << 'EOF'
{% extends "base.html" %}

{% block title %}Simulador de Poupança 2026{% endblock %}
{% block main_class %}form-page{% endblock %}

{% block content %}
<div class="container">
    <h1>Simulador de Poupança 2026</h1>
    <p class="subtitulo">Calcula o valor futuro com juros compostos – planeia as tuas finanças</p>

    <section class="form-card">
        <form method="POST" action="/poupanca">
            {% if erro %}
            <div style="background: #fee; border: 1px solid #c00; color: #c00; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                ⚠️ {{ erro }}
            </div>
            {% endif %}

            <div class="grid">
                <div class="input-group">
                    <label>Valor Inicial (€)</label>
                    <input type="number" name="capital_inicial" step="0.01" min="0" required value="{{ capital_inicial or 1000 }}" placeholder="Ex: 1000">
                </div>
                <div class="input-group">
                    <label>Contribuição Mensal (€)</label>
                    <input type="number" name="contribuicao_mensal" step="0.01" min="0" value="{{ contribuicao_mensal or 100 }}" placeholder="Ex: 100">
                </div>
                <div class="input-group">
                    <label>Taxa de Juro Anual (%)</label>
                    <input type="number" name="taxa_juro" step="0.01" min="0" required value="{{ taxa_juro or 5 }}" placeholder="Ex: 5">
                </div>
                <div class="input-group">
                    <label>Período (anos)</label>
                    <input type="number" name="periodo" step="1" min="1" required value="{{ periodo or 10 }}" placeholder="Ex: 10">
                </div>
            </div>

            <button type="submit" class="btn-main">Simular Poupança</button>
        </form>

        {% if resultado %}
        <div class="resultados visible" style="margin-top: 25px;">
            <div class="grid-res">
                <div class="res-card">
                    <small>Valor Futuro</small>
                    <div class="big-val">€{{ "%.2f"|format(resultado.valor_futuro) }}</div>
                </div>
                <div class="res-card">
                    <small>Total Investido</small>
                    <div class="big-val" style="color: #3b82f6;">€{{ "%.2f"|format(resultado.total_investido) }}</div>
                </div>
            </div>
            <div class="grid-res" style="margin-top: 15px;">
                <div class="res-card">
                    <small>Juros Ganhos</small>
                    <div class="big-val" style="color: #ea580c;">€{{ "%.2f"|format(resultado.juros_ganhos) }}</div>
                </div>
                <div class="res-card">
                    <small>Rentabilidade</small>
                    <div class="big-val" style="color: #2563eb;">{{ "%.1f"|format(resultado.rentabilidade) }}%</div>
                </div>
            </div>

            <div class="info-extra">
                <p><strong>Capital Inicial:</strong> €{{ "%.2f"|format(resultado.capital_inicial) }}</p>
                <p><strong>Contribuição Mensal:</strong> €{{ "%.2f"|format(resultado.contribuicao_mensal) }}</p>
                <p><strong>Taxa de Juro:</strong> {{ resultado.taxa_juro }}%</p>
                <p><strong>Período:</strong> {{ resultado.periodo }} anos</p>
            </div>

            <div style="text-align:center;margin-top:20px;">
                <a href="/poupanca/pdf?capital_inicial={{ capital_inicial }}&contribuicao_mensal={{ contribuicao_mensal }}&taxa_juro={{ taxa_juro }}&periodo={{ periodo }}" target="_blank" style="display:inline-block;background:#2563eb;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600;">📄 Baixar PDF</a>
            </div>

            <div class="bmc-container" style="text-align: center; margin-top: 20px; padding: 15px; background: #f0fdf4; border-radius: 10px; border: 1px solid #059669;">
                <p style="margin: 0 0 10px 0; color: #374151; font-size: 0.95rem;">Esta calculadora foi útil?</p>
                <a href="https://www.buymeacoffee.com/ondoreoku" target="_blank" style="display: inline-block; background: #059669; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 0.9rem;">Paga-me um café</a>
            </div>
        </div>
        {% endif %}
    </section>
</div>
{% endblock %}
EOF

# ====================================================================
# 2. CRIAR UTILS/POUPANCA.PY (LÓGICA DA CALCULADORA)
# ====================================================================
echo "📄 Criando utils/poupanca.py..."

cat > utils/poupanca.py << 'EOF'
def calcular_poupanca(capital_inicial, contribuicao_mensal, taxa_juro, periodo):
    """
    Calcula o valor futuro com juros compostos.
    """
    # Converter taxa para decimal
    taxa = taxa_juro / 100
    # Juros compostos mensais
    taxa_mensal = taxa / 12
    meses = periodo * 12

    # Valor futuro do capital inicial
    valor_futuro = capital_inicial * (1 + taxa_mensal) ** meses

    # Valor futuro das contribuições mensais
    if contribuicao_mensal > 0:
        valor_futuro += contribuicao_mensal * (((1 + taxa_mensal) ** meses - 1) / taxa_mensal)

    total_investido = capital_inicial + (contribuicao_mensal * meses)
    juros_ganhos = valor_futuro - total_investido
    rentabilidade = (juros_ganhos / total_investido) * 100 if total_investido > 0 else 0

    return {
        "capital_inicial": round(capital_inicial, 2),
        "contribuicao_mensal": round(contribuicao_mensal, 2),
        "taxa_juro": round(taxa_juro, 2),
        "periodo": periodo,
        "valor_futuro": round(valor_futuro, 2),
        "total_investido": round(total_investido, 2),
        "juros_ganhos": round(juros_ganhos, 2),
        "rentabilidade": round(rentabilidade, 1)
    }
EOF

# ====================================================================
# 3. ADICIONAR ROTA DA POUPANÇA NO APP.PY
# ====================================================================
echo "🔧 Adicionando rota /poupanca ao app.py..."

# Verificar se a rota já existe para não duplicar
if ! grep -q "@app.route(\"/poupanca\"" app.py; then
    cat >> app.py << 'ROUTE_POUPANCA'

# =============================================================================
# ROTA - SIMULADOR DE POUPANÇA
# =============================================================================
from utils.poupanca import calcular_poupanca

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
ROUTE_POUPANCA
fi

# ====================================================================
# 4. ADICIONAR ROTA PDF DA POUPANÇA
# ====================================================================
echo "🔧 Adicionando rota /poupanca/pdf..."

if ! grep -q "@app.route(\"/poupanca/pdf\"" app.py; then
    cat >> app.py << 'ROUTE_POUPANCA_PDF'

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
ROUTE_POUPANCA_PDF
fi

# ====================================================================
# 5. CORRIGIR PDFS DAS CALCULADORAS EXISTENTES (para usar valores reais)
# ====================================================================
echo "🔧 Corrigindo PDFs nas calculadoras existentes..."

# Substituir links de PDF fixos por links dinâmicos com variáveis

# Salário
sed -i 's|/salario/pdf?salario_bruto=1500|/salario/pdf?salario_bruto={{ bruto }}&regime={{ regime }}|g' templates/salario.html
# Crédito
sed -i 's|/credito/pdf?valor_imovel=200000&entrada=40000&prazo_anos=30|/credito/pdf?valor_imovel={{ valor_imovel }}&entrada={{ entrada }}&prazo_anos={{ prazo_anos }}&spread={{ spread }}&euribor={{ euribor }}|g' templates/credito.html
# Rescisão
sed -i 's|/rescisao/pdf?vencimento_base=1200|/rescisao/pdf?vencimento_base={{ vencimento_base }}&subsidio_alimentacao={{ subsidio_alimentacao }}|g' templates/rescisao.html
# Subsídio
sed -i 's|/subsidio/pdf?media_salarial=1200|/subsidio/pdf?media_salarial={{ media_salarial }}&idade={{ idade }}&meses_desconto={{ meses_desconto }}|g' templates/subsidio.html

# ====================================================================
# 6. ADICIONAR CARD NA HOME (8º CARD)
# ====================================================================
echo "🔧 Adicionando card da Poupança na home..."

# Verificar se o card já existe para não duplicar
if ! grep -q "Simulador de Poupança" templates/home.html; then
    sed -i '/<section class="sugestoes">/,/<\/section>/ {
        /<a href="\/iuc"/a \            <a href="/poupanca" class="card-link">\n                <div class="card">\n                    <h2>Poupança</h2>\n                    <p>Simula o crescimento do teu dinheiro com juros compostos</p>\n                    <span class="card-acao">Simular &rarr;</span>\n                </div>\n            </a>
    }' templates/home.html
fi

# ====================================================================
# 7. ADICIONAR LINK NO MENU (BASE.HTML)
# ====================================================================
echo "🔧 Adicionando link no menu..."

if ! grep -q "/poupanca" templates/base.html; then
    sed -i '/<ul>/a \                <li><a href="/poupanca">Poupança</a></li>' templates/base.html
fi

# ====================================================================
# 8. COMMIT E PUSH
# ====================================================================
echo "📦 Fazendo commit e push..."

git add templates/poupanca.html utils/poupanca.py app.py templates/salario.html templates/credito.html templates/rescisao.html templates/subsidio.html templates/home.html templates/base.html
git commit -m "Add: Calculadora de Poupança + PDFs dinâmicos + 8º card"
git push origin CYBERSEC

echo ""
echo "=========================================="
echo "✅ ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================="
echo ""
echo "📊 O que foi feito:"
echo "  ✅ Criada calculadora de Poupança (juros compostos)"
echo "  ✅ Adicionado 8º card na home (4x2)"
echo "  ✅ PDFs agora usam valores reais dos formulários"
echo "  ✅ Link da Poupança adicionado ao menu"
echo ""
echo "🌐 Acesse: https://calculadoras-portugal.onrender.com"
echo ""
echo "⏳ Aguarde ~1 minuto para o deploy no Render."
echo "=========================================="

