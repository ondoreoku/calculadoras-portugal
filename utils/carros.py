import datetime
import logging

logger = logging.getLogger("seguranca_calculadoras")

def calcular_isv(co2, cilindrada, ano):
    """
    Calcula o ISV de forma 100% local com base nas tabelas oficiais de 2026.
    Evita quebras por APIs externas indisponíveis.
    """
    ano_atual = datetime.datetime.now().year

    try:
        co2 = int(co2)
        cilindrada = int(cilindrada)
        ano = int(ano)
    except (ValueError, TypeError):
        return {"erro": "Os dados introduzidos têm de ser numéricos"}

    if co2 < 0 or co2 > 2000 or cilindrada < 0 or cilindrada > 30000 or ano < 1900 or ano > ano_atual:
        return {"erro": "Valores de entrada fora dos limites de segurança aceitáveis"}

    # 1. Parcela Cilindrada (Tabela Ligeiros Passageiros)
    if cilindrada <= 1000:
        taxa_cc = 1.00
        abate_cc = 780.00
    elif cilindrada <= 1250:
        taxa_cc = 4.90
        abate_cc = 4680.00
    elif cilindrada <= 1750:
        taxa_cc = 5.20
        abate_cc = 5050.00
    else:
        taxa_cc = 9.50
        abate_cc = 12600.00

    componente_cc = (cilindrada * taxa_cc) - abate_cc
    if componente_cc < 0: 
        componente_cc = 0.0

    # 2. Parcela CO2 (WLTP Geral)
    if co2 <= 99:
        taxa_co2 = 0.40
        abate_co2 = 30.00
    elif co2 <= 125:
        taxa_co2 = 1.70
        abate_co2 = 160.00
    elif co2 <= 145:
        taxa_co2 = 4.50
        abate_co2 = 510.00
    elif co2 <= 175:
        taxa_co2 = 14.00
        abate_co2 = 1900.00
    else:
        taxa_co2 = 35.00
        abate_co2 = 5500.00

    componente_co2 = (co2 * taxa_co2) - abate_co2
    if componente_co2 < 0: 
        componente_co2 = 0.0

    # 3. Desconto por Idade do Veículo Usado (Tabela de Desvalorização)
    idade = ano_atual - ano
    if idade <= 1: desconto = 0.10
    elif idade == 2: desconto = 0.20
    elif idade == 3: desconto = 0.28
    elif idade == 4: desconto = 0.35
    elif idade == 5: desconto = 0.43
    elif idade <= 7: desconto = 0.52
    elif idade <= 10: desconto = 0.60
    else: desconto = 0.70

    isv_total = (componente_cc + componente_co2) * (1 - desconto)

    return {
        "isv": float(round(isv_total, 2)),
        "componente_cilindrada": float(round(componente_cc, 2)),
        "componente_co2": float(round(componente_co2, 2)),
        "desconto_idade": float(round(desconto * 100, 1)),
        "nota": "Cálculo local estimado baseado nas tabelas OE2026."
    }

def calcular_iuc(co2, cilindrada, ano, combustivel="gasolina"):
    """
    Calcula o IUC de forma 100% local (Tabelas Categoria B).
    """
    ano_atual = datetime.datetime.now().year

    try:
        co2 = int(co2)
        cilindrada = int(cilindrada)
        ano = int(ano)
    except (ValueError, TypeError):
        return {"erro": "Os dados introduzidos têm de ser numéricos"}

    if co2 < 0 or co2 > 2000 or cilindrada < 0 or cilindrada > 30000 or ano < 1900 or ano > ano_atual:
        return {"erro": "Valores de entrada fora dos limites de segurança aceitáveis"}

    if ano < 2007:
        ano = 2007

    # Cilindrada
    if cilindrada <= 1250: taxa_cilindrada = 31.77
    elif cilindrada <= 1750: taxa_cilindrada = 63.74
    elif cilindrada <= 2500: taxa_cilindrada = 127.35
    else: taxa_cilindrada = 435.84

    # CO2
    taxa_adicional_co2 = 0.0
    if co2 <= 140: taxa_co2 = 65.15
    elif co2 <= 205: taxa_co2 = 97.63
    elif co2 <= 260:
        taxa_co2 = 212.04
        taxa_adicional_co2 = 31.77
    else:
        taxa_co2 = 363.25
        taxa_adicional_co2 = 63.74

    # Coeficiente Ano
    if ano == 2007: coef = 1.0
    elif ano == 2008: coef = 1.05
    elif ano == 2009: coef = 1.10
    else: coef = 1.15

    # Diesel
    adicional_gasoleo = 0.0
    if combustivel == "gasoleo":
        if cilindrada <= 1250: adicional_gasoleo = 0.0
        elif cilindrada <= 1750: adicional_gasoleo = 10.07
        elif cilindrada <= 2500: adicional_gasoleo = 20.12
        else: adicional_gasoleo = 68.85

    iuc_total = ((taxa_cilindrada + taxa_co2) * coef) + taxa_adicional_co2 + adicional_gasoleo

    return {
        "iuc": float(round(iuc_total, 2)),
        "taxa_cilindrada": float(round(taxa_cilindrada, 2)),
        "taxa_co2": float(round(taxa_co2 + taxa_adicional_co2, 2)),
        "coef": float(coef),
        "category": "Categoria B (Ligeiro Passageiros pós-2007)",
        "nota": "Calculado localmente com base nas tabelas oficiais de 2026."
    }