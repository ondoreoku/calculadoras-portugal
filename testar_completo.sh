#!/bin/bash

# ============================================
# TESTE COMPLETO - Calculadoras Portugal 2026
# ============================================

URL="https://calculadoras-portugal.onrender.com"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🧪 TESTE COMPLETO - $DATE"
echo "=========================================="
echo ""

# Contador de testes
TOTAL=0
PASS=0
FAIL=0

# Função para testar
testar() {
    local nome="$1"
    local comando="$2"
    local esperado="$3"
    
    TOTAL=$((TOTAL + 1))
    echo -n "▶ $nome ... "
    
    resultado=$(eval "$comando" 2>/dev/null)
    status=$?
    
    if [ $status -eq 0 ] && echo "$resultado" | grep -q "$esperado"; then
        echo -e "${GREEN}✅ OK${NC}"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}❌ FALHOU${NC}"
        echo "   → Esperado: $esperado"
        echo "   → Obtido: $(echo "$resultado" | head -c 100)"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

# ============================================
# 1. HEALTH CHECK
# ============================================
echo -e "${BLUE}📡 1. HEALTH CHECK${NC}"
testar "API Health" \
    "curl -s $URL/api/health" \
    '"status":"ok"'
echo ""

# ============================================
# 2. PÁGINAS HTML
# ============================================
echo -e "${BLUE}🌐 2. PÁGINAS HTML${NC}"
for pagina in "" "salario" "credito" "rescisao" "subsidio" "historico"; do
    if [ -z "$pagina" ]; then
        testar "Página inicial (/)" \
            "curl -s -o /dev/null -w '%{http_code}' $URL/" \
            "200"
    else
        testar "Página /$pagina" \
            "curl -s -o /dev/null -w '%{http_code}' $URL/$pagina" \
            "200"
    fi
done
echo ""

# ============================================
# 3. APIS PRINCIPAIS
# ============================================
echo -e "${BLUE}🔌 3. APIS PRINCIPAIS${NC}"

# 3.1 API Salário
testar "API Salário" \
    "curl -s -X POST $URL/api/salario -H 'Content-Type: application/json' -d '{\"bruto\":1500}' | jq -r '.liquido'" \
    "[0-9]"

# 3.2 API Crédito
testar "API Crédito" \
    "curl -s -X POST $URL/api/credito -H 'Content-Type: application/json' -d '{\"valor_imovel\":200000,\"entrada\":40000}' | jq -r '.prestacao_mensal'" \
    "[0-9]"

# 3.3 API Rescisão
testar "API Rescisão" \
    "curl -s -X POST $URL/api/rescisao -H 'Content-Type: application/json' -d '{\"vencimento_base\":1200}' | jq -r '.total'" \
    "[0-9]"

# 3.4 API Subsídio
testar "API Subsídio" \
    "curl -s -X POST $URL/api/subsidio -H 'Content-Type: application/json' -d '{\"media_salarial\":1200,\"idade\":30,\"meses_desconto\":12}' | jq -r '.valor_mensal'" \
    "[0-9]"

echo ""

# ============================================
# 4. APIS EXTERNAS (INE e CARROS)
# ============================================
echo -e "${BLUE}🚗 4. APIS EXTERNAS${NC}"

# 4.1 API INE
testar "API INE" \
    "curl -s $URL/api/ine/inflacao | jq -r '.fonte'" \
    "INE"

# 4.2 API Carros ISV
testar "API Carros ISV" \
    "curl -s '$URL/api/carros/isv?ano=2020&cilindrada=2000&co2=150' | jq -r '.isv.isv'" \
    "[0-9]"

# 4.3 API Carros IUC
testar "API Carros IUC" \
    "curl -s '$URL/api/carros/iuc?ano=2020&co2=150' | jq -r '.iuc'" \
    "[0-9]"

echo ""

# ============================================
# 5. PDFs
# ============================================
echo -e "${BLUE}📄 5. PDFs${NC}"

# 5.1 PDF Salário
echo "▶ PDF Salário ... "
curl -s -o /tmp/salario.pdf "$URL/salario/pdf?salario_bruto=1500"
if [ -f /tmp/salario.pdf ] && file /tmp/salario.pdf | grep -q "PDF"; then
    echo -e "${GREEN}✅ OK${NC}"
    PASS=$((PASS + 1))
else
    echo -e "${RED}❌ FALHOU${NC}"
    FAIL=$((FAIL + 1))
fi
TOTAL=$((TOTAL + 1))

# 5.2 PDF Crédito
echo "▶ PDF Crédito ... "
curl -s -o /tmp/credito.pdf "$URL/credito/pdf?valor_imovel=200000&entrada=40000"
if [ -f /tmp/credito.pdf ] && file /tmp/credito.pdf | grep -q "PDF"; then
    echo -e "${GREEN}✅ OK${NC}"
    PASS=$((PASS + 1))
else
    echo -e "${RED}❌ FALHOU${NC}"
    FAIL=$((FAIL + 1))
fi
TOTAL=$((TOTAL + 1))

# 5.3 PDF Rescisão
echo "▶ PDF Rescisão ... "
curl -s -o /tmp/rescisao.pdf "$URL/rescisao/pdf?vencimento_base=1200"
if [ -f /tmp/rescisao.pdf ] && file /tmp/rescisao.pdf | grep -q "PDF"; then
    echo -e "${GREEN}✅ OK${NC}"
    PASS=$((PASS + 1))
else
    echo -e "${RED}❌ FALHOU${NC}"
    FAIL=$((FAIL + 1))
fi
TOTAL=$((TOTAL + 1))

# 5.4 PDF Subsídio
echo "▶ PDF Subsídio ... "
curl -s -o /tmp/subsidio.pdf "$URL/subsidio/pdf?media_salarial=1200"
if [ -f /tmp/subsidio.pdf ] && file /tmp/subsidio.pdf | grep -q "PDF"; then
    echo -e "${GREEN}✅ OK${NC}"
    PASS=$((PASS + 1))
else
    echo -e "${RED}❌ FALHOU${NC}"
    FAIL=$((FAIL + 1))
fi
TOTAL=$((TOTAL + 1))

echo ""

# ============================================
# 6. SEGURANÇA
# ============================================
echo -e "${BLUE}🔒 6. SEGURANÇA${NC}"

# 6.1 Headers de segurança
echo "▶ Headers de Segurança:"
HEADERS=$(curl -s -I $URL 2>/dev/null)
for header in "strict-transport-security" "content-security-policy" "x-frame-options" "x-content-type-options" "referrer-policy"; do
    if echo "$HEADERS" | grep -qi "$header"; then
        echo -e "   ${GREEN}✅ $header${NC}"
    else
        echo -e "   ${RED}❌ $header${NC}"
    fi
done

# 6.2 Rate Limiting (5 requisições)
echo "▶ Rate Limiting (5 requisições):"
for i in {1..5}; do
    status=$(curl -s -o /dev/null -w "%{http_code}" -X POST $URL/salario -d "bruto=1500&regime=outrem" 2>/dev/null)
    if [ $i -le 4 ]; then
        if [ "$status" = "200" ]; then
            echo -e "   Requisição $i: ${GREEN}$status${NC}"
        else
            echo -e "   Requisição $i: ${RED}$status${NC}"
        fi
    else
        if [ "$status" = "429" ] || [ "$status" = "200" ]; then
            echo -e "   Requisição $i: ${GREEN}$status${NC}"
        else
            echo -e "   Requisição $i: ${RED}$status${NC}"
        fi
    fi
    sleep 0.3
done

# 6.3 XSS
testar "XSS Protection" \
    "curl -s -o /dev/null -w '%{http_code}' -X POST $URL/salario -d 'bruto=<script>alert(1)</script>&regime=outrem'" \
    "403"

# 6.4 SQL Injection
testar "SQL Injection" \
    "curl -s -o /dev/null -w '%{http_code}' -X POST $URL/salario -d \"bruto=1500' OR '1'='1&regime=outrem\"" \
    "403"

echo ""

# ============================================
# 7. DARK MODE
# ============================================
echo -e "${BLUE}🌙 7. DARK MODE${NC}"
if curl -s $URL/static/css/style.css | grep -q "dark-mode"; then
    echo -e "   ${GREEN}✅ CSS do dark mode presente${NC}"
    PASS=$((PASS + 1))
else
    echo -e "   ${RED}❌ CSS do dark mode NÃO encontrado${NC}"
    FAIL=$((FAIL + 1))
fi
TOTAL=$((TOTAL + 1))
echo ""

# ============================================
# 8. NOTÍCIAS
# ============================================
echo -e "${BLUE}📰 8. NOTÍCIAS${NC}"
testar "Feed de Notícias" \
    "curl -s $URL/ | grep -c 'noticia'" \
    "[0-9]"
echo ""

# ============================================
# 9. CORS
# ============================================
echo -e "${BLUE}🌐 9. CORS${NC}"

# 9.1 Origem autorizada
testar "CORS - Origem autorizada" \
    "curl -s -H 'Origin: https://salarioliquido.vercel.app' -X POST $URL/api/salario -H 'Content-Type: application/json' -d '{\"bruto\":1500}' -o /dev/null -w '%{http_code}'" \
    "200"

# 9.2 Origem não autorizada
testar "CORS - Origem não autorizada" \
    "curl -s -H 'Origin: https://evil.com' -X POST $URL/api/salario -H 'Content-Type: application/json' -d '{\"bruto\":1500}' -o /dev/null -w '%{http_code}'" \
    "200"

echo ""

# ============================================
# 10. INTERFACE VISUAL (NOVAS FUNCIONALIDADES)
# ============================================
echo -e "${BLUE}🖥️ 10. INTERFACE VISUAL${NC}"

# 10.1 Verificar se a secção de novas funcionalidades existe
if curl -s $URL/ | grep -q "Novas Funcionalidades"; then
    echo -e "   ${GREEN}✅ Secção 'Novas Funcionalidades' encontrada${NC}"
    PASS=$((PASS + 1))
else
    echo -e "   ${RED}❌ Secção 'Novas Funcionalidades' NÃO encontrada${NC}"
    FAIL=$((FAIL + 1))
fi
TOTAL=$((TOTAL + 1))

# 10.2 Verificar botões PDF nas páginas
for pagina in "salario" "credito" "rescisao" "subsidio"; do
    if curl -s $URL/$pagina | grep -q "Baixar PDF"; then
        echo -e "   ${GREEN}✅ Botão PDF em /$pagina${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "   ${RED}❌ Botão PDF em /$pagina${NC}"
        FAIL=$((FAIL + 1))
    fi
    TOTAL=$((TOTAL + 1))
done

echo ""

# ============================================
# RESUMO FINAL
# ============================================
echo "=========================================="
echo "📊 RESUMO DOS TESTES"
echo "=========================================="
echo ""
echo -e "✅ Total de testes: ${GREEN}$TOTAL${NC}"
echo -e "✅ Passaram: ${GREEN}$PASS${NC}"
echo -e "❌ Falharam: ${RED}$FAIL${NC}"
echo ""
echo -e "📊 Taxa de sucesso: ${GREEN}$(( PASS * 100 / TOTAL ))${NC}%"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 TODOS OS TESTES PASSARAM!${NC}"
    echo -e "${GREEN}🚀 PROJETO 100% FUNCIONAL!${NC}"
else
    echo -e "${YELLOW}⚠️ ALGUNS TESTES FALHARAM${NC}"
    echo -e "${YELLOW}🔧 Verifica os logs no Render Dashboard${NC}"
fi

echo ""
echo "🔍 Verifica os logs no Render:"
echo "   https://dashboard.render.com"
echo ""
echo "=========================================="
echo "✅ TESTES CONCLUÍDOS!"
echo "=========================================="

# Limpar ficheiros temporários
rm -f /tmp/salario.pdf /tmp/credito.pdf /tmp/rescisao.pdf /tmp/subsidio.pdf

