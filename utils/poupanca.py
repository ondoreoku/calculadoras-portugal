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
