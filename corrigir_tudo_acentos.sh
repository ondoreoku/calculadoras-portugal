#!/bin/bash
set -e

echo "🔤 CORREÇÃO COMPLETA DE ACENTOS E CEDILHAS"
echo "==========================================="
echo ""

# Backup
echo "📦 Criando backup..."
cp -r templates templates_backup_total_$(date +%Y%m%d_%H%M%S)
cp utils/noticias.py utils/noticias.py.bak
echo "✅ Backup criado"
echo ""

# ============================================================================
# CORRIGIR TODOS OS TEMPLATES HTML
# ============================================================================
echo "🔧 Corrigindo templates HTML..."

# home.html
sed -i 's/Inicio -- Calculadoras/Início — Calculadoras/g' templates/home.html
sed -i 's/Salario Liquido/Salário Líquido/g' templates/home.html
sed -i 's/Credito Habitacao/Crédito Habitação/g' templates/home.html
sed -i 's/Rescisao/Rescisão/g' templates/home.html
sed -i 's/Subsidio Desemprego/Subsídio de Desemprego/g' templates/home.html
sed -i 's/Inflacao/Inflação/g' templates/home.html
sed -i 's/Poupanca/Poupança/g' templates/home.html
sed -i 's/Calcula o teu salario/Calcula o teu salário/g' templates/home.html
sed -i 's/apos descontos/após descontos/g' templates/home.html
sed -i 's/Seguranca Social/Segurança Social/g' templates/home.html
sed -i 's/Calcula a prestacao/Calcula a prestação/g' templates/home.html
sed -i 's/emprestimo bancario/empréstimo bancário/g' templates/home.html
sed -i 's/Calcula a indemnizacao/Calcula a indemnização/g' templates/home.html
sed -i 's/Calcula o valor do apoio/Calcula o valor do apoio/g' templates/home.html
sed -i 's/Consulta a taxa de inflacao/Consulta a taxa de inflação/g' templates/home.html
sed -i 's/Calcula o Imposto Sobre Veiculos/Calcula o Imposto Sobre Veículos/g' templates/home.html
sed -i 's/Calcula o Imposto Unico de Circulacao/Calcula o Imposto Único de Circulação/g' templates/home.html
sed -i 's/Simula o crescimento/Simula o crescimento/g' templates/home.html
sed -i 's/Noticias Relevantes/Notícias Relevantes/g' templates/home.html
sed -i 's/Sem noticias/Sem notícias/g' templates/home.html
sed -i 's/disponiveis/disponíveis/g' templates/home.html
sed -i 's/Atualizar feed/Atualizar feed/g' templates/home.html
sed -i 's/Novas Funcionalidades/Novas Funcionalidades/g' templates/home.html
sed -i 's/Estatisticas/Estatísticas/g' templates/home.html
sed -i 's/Historico/Histórico/g' templates/home.html
sed -i 's/Atualizar Noticias/Atualizar Notícias/g' templates/home.html

# base.html
sed -i 's/Inflacao/Inflação/g' templates/base.html
sed -i 's/Poupanca/Poupança/g' templates/base.html
sed -i 's/Desemprego/Desemprego/g' templates/base.html

# historico.html
sed -i 's/Historico de Calculos/Histórico de Cálculos/g' templates/historico.html
sed -i 's/Registo de todos os calculos/Registo de todos os cálculos/g' templates/historico.html

# salario.html
sed -i 's/Calculadora de Salario/Calculadora de Salário/g' templates/salario.html
sed -i 's/Calcula o teu salario/Calcula o teu salário/g' templates/salario.html
sed -i 's/apos descontos/após descontos/g' templates/salario.html
sed -i 's/Seguranca Social/Segurança Social/g' templates/salario.html
sed -i 's/Salario Bruto/Salário Bruto/g' templates/salario.html
sed -i 's/Subsidio Alimentação/Subsídio Alimentação/g' templates/salario.html
sed -i 's/Regime de Trabalho/Regime de Trabalho/g' templates/salario.html
sed -i 's/Conta de Outrem/Conta de Outrem/g' templates/salario.html
sed -i 's/Trabalhador Independente/Trabalhador Independente/g' templates/salario.html
sed -i 's/Coeficiente de Atividade/Coeficiente de Atividade/g' templates/salario.html
sed -i 's/Retencao IRS/Retenção IRS/g' templates/salario.html
sed -i 's/Isento de Seguranca Social/Isento de Segurança Social/g' templates/salario.html
sed -i 's/Salario Liquido/Salário Líquido/g' templates/salario.html
sed -i 's/Seguranca Social/Segurança Social/g' templates/salario.html
sed -i 's/Taxa Efetiva IRS/Taxa Efetiva IRS/g' templates/salario.html
sed -i 's/Rendimento Tributavel/Rendimento Tributável/g' templates/salario.html

# credito.html
sed -i 's/Simulador de Credito/Simulador de Crédito/g' templates/credito.html
sed -i 's/Calcula a prestacao/Calcula a prestação/g' templates/credito.html
sed -i 's/emprestimo bancario/empréstimo bancário/g' templates/credito.html
sed -i 's/Valor do Imovel/Valor do Imóvel/g' templates/credito.html
sed -i 's/Entrada Inicial/Entrada Inicial/g' templates/credito.html
sed -i 's/Prazo/Prazo/g' templates/credito.html
sed -i 's/Spread do Banco/Spread do Banco/g' templates/credito.html
sed -i 's/Euribor Atual/Euribor Atual/g' templates/credito.html
sed -i 's/Calcular Prestacao/Calcular Prestação/g' templates/credito.html
sed -i 's/Prestacao Mensal/Prestação Mensal/g' templates/credito.html
sed -i 's/Montante Financiado/Montante Financiado/g' templates/credito.html
sed -i 's/Taxa Anual/Taxa Anual/g' templates/credito.html
sed -i 's/Numero de Prestacoes/Número de Prestações/g' templates/credito.html
sed -i 's/Total de Juros/Total de Juros/g' templates/credito.html
sed -i 's/Tabela de Amortizacao/Tabela de Amortização/g' templates/credito.html

# rescisao.html
sed -i 's/Calculadora de Rescisao/Calculadora de Rescisão/g' templates/rescisao.html
sed -i 's/Calcula a indemnizacao/Calcula a indemnização/g' templates/rescisao.html
sed -i 's/Vencimento Base/Vencimento Base/g' templates/rescisao.html
sed -i 's/Subsidio Alimentacao/Subsídio Alimentação/g' templates/rescisao.html
sed -i 's/Data de Inicio/Data de Início/g' templates/rescisao.html
sed -i 's/Data de Fim/Data de Fim/g' templates/rescisao.html
sed -i 's/Motivo da Rescisao/Motivo da Rescisão/g' templates/rescisao.html
sed -i 's/Caducidade de Termo/Caducidade de Termo/g' templates/rescisao.html
sed -i 's/Despedimento Coletivo/Despedimento Coletivo/g' templates/rescisao.html
sed -i 's/Justa Causa/Justa Causa/g' templates/rescisao.html
sed -i 's/Mutuo Acordo/Mútuo Acordo/g' templates/rescisao.html
sed -i 's/Meses em Lay-off/Meses em Lay-off/g' templates/rescisao.html
sed -i 's/Ferias Vencidas/Férias Vencidas/g' templates/rescisao.html
sed -i 's/Horas de Formacao/Horas de Formação/g' templates/rescisao.html
sed -i 's/Calcular Rescisao/Calcular Rescisão/g' templates/rescisao.html
sed -i 's/Total a Receber/Total a Receber/g' templates/rescisao.html
sed -i 's/Anos de Trabalho/Anos de Trabalho/g' templates/rescisao.html
sed -i 's/Compensacao Antiguidade/Compensação Antiguidade/g' templates/rescisao.html
sed -i 's/Proporcional Natal/Proporcional Natal/g' templates/rescisao.html
sed -i 's/Proporcional Ferias/Proporcional Férias/g' templates/rescisao.html
sed -i 's/Ferias Nao Gozadas/Férias Não Gozadas/g' templates/rescisao.html
sed -i 's/Formacao/Formação/g' templates/rescisao.html
sed -i 's/Ultimo Mes/Último Mês/g' templates/rescisao.html

# subsidio.html
sed -i 's/Simulador de Subsidio/Simulador de Subsídio/g' templates/subsidio.html
sed -i 's/Calcule o valor/Calcule o valor/g' templates/subsidio.html
sed -i 's/Media dos Salarios/Média dos Salários/g' templates/subsidio.html
sed -i 's/Idade do Beneficiario/Idade do Beneficiário/g' templates/subsidio.html
sed -i 's/Meses de Descontos/Meses de Descontos/g' templates/subsidio.html
sed -i 's/Calcular Apoio/Calcular Apoio/g' templates/subsidio.html
sed -i 's/Valor Mensal/Valor Mensal/g' templates/subsidio.html
sed -i 's/Duracao do Apoio/Duração do Apoio/g' templates/subsidio.html
sed -i 's/Limite Minimo/Limite Mínimo/g' templates/subsidio.html
sed -i 's/Limite Maximo/Limite Máximo/g' templates/subsidio.html

# inflacao.html
sed -i 's/Calculadora de Inflacao/Calculadora de Inflação/g' templates/inflacao.html
sed -i 's/Consulta a taxa de inflacao/Consulta a taxa de inflação/g' templates/inflacao.html
sed -i 's/Data de referencia/Data de referência/g' templates/inflacao.html
sed -i 's/Consultar Inflacao/Consultar Inflação/g' templates/inflacao.html
sed -i 's/Inflacao/Inflação/g' templates/inflacao.html
sed -i 's/Periodo/Período/g' templates/inflacao.html

# isv.html
sed -i 's/Calculadora de ISV/Calculadora de ISV/g' templates/isv.html
sed -i 's/Calcula o Imposto Sobre Veiculos/Calcula o Imposto Sobre Veículos/g' templates/isv.html
sed -i 's/Ano do Veiculo/Ano do Veículo/g' templates/isv.html
sed -i 's/Cilindrada/Cilindrada/g' templates/isv.html
sed -i 's/Emissoes CO2/Emissões CO₂/g' templates/isv.html
sed -i 's/Calcular ISV/Calcular ISV/g' templates/isv.html
sed -i 's/ISV Total/ISV Total/g' templates/isv.html
sed -i 's/Componente Ambiental/Componente Ambiental/g' templates/isv.html
sed -i 's/Componente Cilindrada/Componente Cilindrada/g' templates/isv.html
sed -i 's/Reducao por idade/Redução por idade/g' templates/isv.html
sed -i 's/Anos de idade/Anos de idade/g' templates/isv.html

# iuc.html
sed -i 's/Calculadora de IUC/Calculadora de IUC/g' templates/iuc.html
sed -i 's/Calcula o Imposto Unico/Calcula o Imposto Único/g' templates/iuc.html
sed -i 's/Ano do Veiculo/Ano do Veículo/g' templates/iuc.html
sed -i 's/Emissoes CO2/Emissões CO₂/g' templates/iuc.html
sed -i 's/Calcular IUC/Calcular IUC/g' templates/iuc.html
sed -i 's/IUC Total/IUC Total/g' templates/iuc.html
sed -i 's/Componente CO2/Componente CO₂/g' templates/iuc.html
sed -i 's/Componente Cilindrada/Componente Cilindrada/g' templates/iuc.html

# poupanca.html
sed -i 's/Simulador de Poupanca/Simulador de Poupança/g' templates/poupanca.html
sed -i 's/Calcula o valor futuro/Calcula o valor futuro/g' templates/poupanca.html
sed -i 's/juros compostos/juros compostos/g' templates/poupanca.html
sed -i 's/planeia as tuas financas/planeia as tuas finanças/g' templates/poupanca.html
sed -i 's/Valor Inicial/Valor Inicial/g' templates/poupanca.html
sed -i 's/Contribuicao Mensal/Contribuição Mensal/g' templates/poupanca.html
sed -i 's/Taxa de Juro Anual/Taxa de Juro Anual/g' templates/poupanca.html
sed -i 's/Periodo/Período/g' templates/poupanca.html
sed -i 's/Simular Poupanca/Simular Poupança/g' templates/poupanca.html
sed -i 's/Valor Futuro/Valor Futuro/g' templates/poupanca.html
sed -i 's/Total Investido/Total Investido/g' templates/poupanca.html
sed -i 's/Juros Ganhos/Juros Ganhos/g' templates/poupanca.html
sed -i 's/Rentabilidade/Rentabilidade/g' templates/poupanca.html
sed -i 's/Capital Inicial/Capital Inicial/g' templates/poupanca.html
sed -i 's/Contribuicao Mensal/Contribuição Mensal/g' templates/poupanca.html
sed -i 's/Taxa de Juro/Taxa de Juro/g' templates/poupanca.html
sed -i 's/Periodo/Período/g' templates/poupanca.html

echo "✅ Templates HTML corrigidos"
echo ""

# ============================================================================
# CORRIGIR utils/noticias.py
# ============================================================================
echo "🔧 Corrigindo utils/noticias.py..."

sed -i 's/mantem-se/mantém-se/g' utils/noticias.py
sed -i 's/afetando calculos/afetando cálculos/g' utils/noticias.py
sed -i 's/subsidio/subsídio/g' utils/noticias.py
sed -i 's/Tabelas de retencao/Tabelas de retenção/g' utils/noticias.py
sed -i 's/aplicaveis/aplicáveis/g' utils/noticias.py
sed -i 's/Teu salario/Teu salário/g' utils/noticias.py
sed -i 's/Taxas de juro/Taxas de juro/g' utils/noticias.py
sed -i 's/credito habitacao/crédito habitação/g' utils/noticias.py
sed -i 's/revisoes de taxas variaveis/revisões de taxas variáveis/g' utils/noticias.py
sed -i 's/criterios/critérios/g' utils/noticias.py
sed -i 's/reforma antecipada/reforma antecipada/g' utils/noticias.py
sed -i 's/nao sofrem alteracoes/não sofrem alterações/g' utils/noticias.py
sed -i 's/Salario minimo/Salário mínimo/g' utils/noticias.py
sed -i 's/discussao/discussão/g' utils/noticias.py
sed -i 's/Indice de precos/Índice de preços/g' utils/noticias.py
sed -i 's/mantem tendencia/mantém tendência/g' utils/noticias.py
sed -i 's/desaceleracao/desaceleração/g' utils/noticias.py
sed -i 's/poder de compra/poder de compra/g' utils/noticias.py
sed -i 's/familias/famílias/g' utils/noticias.py
sed -i 's/monitoriza margens/monitoriza margens/g' utils/noticias.py
sed -i 's/concessao de credito/concessão de crédito/g' utils/noticias.py
sed -i 's/Trabalhadores independentes/Trabalhadores independentes/g' utils/noticias.py
sed -i 's/solicitar subsidio/solicitar subsídio/g' utils/noticias.py
sed -i 's/ferias/férias/g' utils/noticias.py
sed -i 's/requisitos de descontos/requisitos de descontos/g' utils/noticias.py
sed -i 's/Seguranca Social/Segurança Social/g' utils/noticias.py
sed -i 's/aplicaveis/aplicáveis/g' utils/noticias.py
sed -i 's/trabalhadores por conta de outrem/trabalhadores por conta de outrem/g' utils/noticias.py

echo "✅ utils/noticias.py corrigido"
echo ""

# ============================================================================
# COMMIT E PUSH
# ============================================================================
echo " A fazer commit e push..."
git add templates/ utils/noticias.py
git commit -m "fix: Adiciona TODOS os acentos e cedilhas em todo o site

- Corrigidos todos os templates HTML (home, base, salario, credito, rescisao, subsidio, historico, inflacao, isv, iuc, poupanca)
- Corrigido utils/noticias.py (títulos e resumos das notícias)
- Incluídos: Início, Salário, Crédito, Rescisão, Subsídio, Inflação, Poupança, Histórico, Notícias, etc."
git push origin grid-home-e-melhorias

echo ""
echo "=========================================="
echo "✅ CORREÇÃO COMPLETA CONCLUÍDA!"
echo "=========================================="
echo ""
echo "📊 O que foi corrigido:"
echo "  ✅ templates/home.html"
echo "  ✅ templates/base.html"
echo "  ✅ templates/salario.html"
echo "  ✅ templates/credito.html"
echo "  ✅ templates/rescisao.html"
echo "  ✅ templates/subsidio.html"
echo "  ✅ templates/historico.html"
echo "  ✅ templates/inflacao.html"
echo "  ✅ templates/isv.html"
echo "  ✅ templates/iuc.html"
echo "  ✅ templates/poupanca.html"
echo "  ✅ utils/noticias.py"
echo ""
echo "🌐 Verifica o site em:"
echo "   https://calculadoras-portugal.onrender.com"
echo ""
echo " Branch: grid-home-e-melhorias"
echo "=========================================="
