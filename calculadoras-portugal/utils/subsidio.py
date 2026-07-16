def calcular_subsidio(media_salarial, idade, meses_desconto):
    """
    Calcula o valor mensal e duração do subsídio de desemprego.
    
    Args:
        media_salarial: Média dos últimos 12 meses (€)
        idade: Idade do trabalhador (anos)
        meses_desconto: Meses com descontos para a SS
    
    Returns:
        dict com valor_mensal, duracao, limite_min, limite_max
    """
    
    # Valor base: 65% da média
    valor_mensal = media_salarial * 0.65
    
    # Limites IAS 2026 (Estimativa)
    ias = 510.00
    limite_min = ias           # 100% do IAS
    limite_max = ias * 2.5     # 2.5x o IAS
    
    # Aplicar limites
    if valor_mensal < limite_min:
        valor_mensal = limite_min
    if valor_mensal > limite_max:
        valor_mensal = limite_max
    
    # Estimativa de Duração (Regras Simplificadas 2026)
    if idade < 30:
        if meses_desconto >= 12:
            duracao = "270 dias (9 meses)"
        else:
            duracao = "Pode não cumprir prazo de garantia"
    elif idade < 40:
        duracao = "365 dias (12 meses)"
    elif idade < 50:
        duracao = "540 dias (18 meses)"
    else:
        duracao = "720 dias (24 meses) ou mais"
    
    return {
        "valor_mensal": round(valor_mensal, 2),
        "duracao": duracao,
        "limite_min": limite_min,
        "limite_max": limite_max,
        "ias": ias
    }