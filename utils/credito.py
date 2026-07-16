"""
================================================================================
CREDITO.PY — Simulador de Crédito Habitação (Sistema Francês de Amortização)
================================================================================

O QUE FAZ:
    Calcula a prestação mensal, montante financiado e MTIC (montante total)
    de um crédito habitação usando a fórmula Price.

FÓRMULA PRICE:
    P = M * (i / (1 - (1 + i)^(-n)))

    Onde:
      P = prestação mensal
      M = montante financiado (valor do imóvel - entrada)
      i = taxa de juro mensal (taxa anual / 12 / 100)
      n = número total de prestações (anos * 12)

CASO ESPECIAL:
    Se a taxa de juro for 0%, a prestação é simplesmente M / n.

INPUTS:
    — valor_imovel: valor total do imóvel (€)
    — entrada: valor da entrada inicial (€)
    — prazo_anos: prazo do empréstimo em anos
    — spread: spread do banco (%)
    — euribor: taxa Euribor atual (%)

OUTPUTS:
    — prestacao_mensal: valor da prestação mensal (€)
    — montante_financiado: valor efetivamente emprestado (€)
    — mtic: montante total de juros pagos (€)
    — taxa_anual: taxa de juro anual total (spread + euribor) (%)
    — numero_prestacoes: total de prestações
"""

import math


def calcular_credito(valor_imovel, entrada, prazo_anos, spread, euribor):
    """
    Calcula o crédito habitação usando o sistema Price.

    Args:
        valor_imovel (float): valor total do imóvel em euros
        entrada (float): valor da entrada em euros
        prazo_anos (int): prazo do empréstimo em anos
        spread (float): spread do banco em percentagem (ex: 1.5)
        euribor (float): taxa Euribor em percentagem (ex: 3.5)

    Returns:
        dict: resultado com prestação, montante financiado, MTIC, etc.
    """

    # --- Passo 1: Calcular montante financiado ---
    montante = valor_imovel - entrada

    # --- Passo 2: Calcular taxa de juro anual ---
    taxa_anual = spread + euribor

    # --- Passo 3: Converter taxa anual para mensal ---
    taxa_mensal = (taxa_anual / 100) / 12

    # --- Passo 4: Calcular número total de prestações ---
    numero_prestacoes = prazo_anos * 12

    # --- Passo 5: Calcular prestação mensal (Fórmula Price) ---
    if taxa_mensal > 0:
        prestacao = montante * (taxa_mensal / (1 - math.pow(1 + taxa_mensal, -numero_prestacoes)))
    else:
        prestacao = montante / numero_prestacoes

    # --- Passo 6: Calcular MTIC ---
    mtic = prestacao * numero_prestacoes

    # --- Passo 7: Calcular total de juros pagos ---
    total_juros = mtic - montante

    return {
        "prestacao_mensal": round(prestacao, 2),
        "montante_financiado": round(montante, 2),
        "mtic": round(mtic, 2),
        "total_juros": round(total_juros, 2),
        "taxa_anual": round(taxa_anual, 2),
        "numero_prestacoes": numero_prestacoes,
        "valor_imovel": round(valor_imovel, 2),
        "entrada": round(entrada, 2),
        "prazo_anos": prazo_anos,
        "spread": spread,
        "euribor": euribor,
    }


def calcular_tabela_amortizacao(valor_imovel, entrada, prazo_anos, spread, euribor, limite=12):
    """
    Gera a tabela de amortização (primeiras N prestações).

    Args:
        limite (int): número de prestações a mostrar (padrão: 12)

    Returns:
        list: lista de dicionários com cada prestação (mês, capital, juros, saldo)
    """

    resultado = calcular_credito(valor_imovel, entrada, prazo_anos, spread, euribor)

    montante = resultado["montante_financiado"]
    taxa_mensal = (resultado["taxa_anual"] / 100) / 12
    prestacao = resultado["prestacao_mensal"]
    numero_prestacoes = resultado["numero_prestacoes"]

    tabela = []
    saldo_devedor = montante

    for mes in range(1, min(limite + 1, numero_prestacoes + 1)):
        if taxa_mensal > 0:
            juros_mes = saldo_devedor * taxa_mensal
        else:
            juros_mes = 0

        capital_mes = prestacao - juros_mes
        saldo_devedor -= capital_mes

        tabela.append({
            "mes": mes,
            "prestacao": round(prestacao, 2),
            "capital": round(capital_mes, 2),
            "juros": round(juros_mes, 2),
            "saldo_devedor": round(max(saldo_devedor, 0), 2)
        })

    return tabela


if __name__ == "__main__":
    print("=" * 60)
    print("  TESTE: Crédito Habitação")
    print("=" * 60)

    r = calcular_credito(200000, 40000, 30, 1.5, 3.5)
    print("Valor do imóvel: €" + str(r["valor_imovel"]))
    print("Entrada: €" + str(r["entrada"]))
    print("Montante financiado: €" + str(r["montante_financiado"]))
    print("Taxa anual: " + str(r["taxa_anual"]) + "%")
    print("Prestação mensal: €" + str(r["prestacao_mensal"]))
    print("Número de prestações: " + str(r["numero_prestacoes"]))
    print("MTIC: €" + str(r["mtic"]))
    print("Total de juros: €" + str(r["total_juros"]))
