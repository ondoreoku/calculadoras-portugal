"""
RESCISAO.PY - Calculadora de Rescisao de Contrato
"""

from datetime import datetime


def calcular_rescisao(vencimento_base, subsidio_alimentacao=6.0,
                      data_inicio="2020-01-15", data_fim="2026-07-16",
                      motivo="caducidade_termo", meses_layoff=0,
                      ferias_vencidas=0, horas_formacao=0):
    """
    Calcula os valores da rescisao de contrato de trabalho.
    """
    
    # Converter datas
    d_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
    d_fim = datetime.strptime(data_fim, "%Y-%m-%d")
    
    # Calcular anos de trabalho
    dias_totais = (d_fim - d_inicio).days
    anos_trabalho = dias_totais / 365.25
    
    # Dias trabalhados no ultimo mes
    dias_ultimo_mes = d_fim.day
    
    # Valor dia de trabalho
    valor_dia = vencimento_base / 22  # 22 dias uteis por mes
    
    # === COMPENSACAO POR ANTIGUIDADE ===
    if motivo in ["despedimento_coletivo", "caducidade_termo"]:
        # 1 mes de vencimento por ano de trabalho
        compensacao_antiguidade = vencimento_base * anos_trabalho
    elif motivo == "justa_causa_trabalhador":
        # Justa causa do trabalhador: 15 dias por ano
        compensacao_antiguidade = (vencimento_base / 2) * anos_trabalho
    elif motivo == "mutuo_acordo":
        # Mutuo acordo: negociavel, usamos 0.5 meses por ano como base
        compensacao_antiguidade = (vencimento_base * 0.5) * anos_trabalho
    else:
        compensacao_antiguidade = 0
    
    # === PROPORCIONAIS ===
    # Subsidio de Natal (pago em novembro, proporcional aos meses trabalhados)
    meses_ate_fim = d_fim.month
    proporcional_natal = (vencimento_base / 12) * meses_ate_fim
    
    # Subsidio de Ferias (proporcional)
    proporcional_ferias = (vencimento_base / 12) * meses_ate_fim
    
    # === FERIAS NAO GOZADAS ===
    # 2 dias por mes trabalhado, ou valor proporcional
    ferias_nao_gozadas = (vencimento_base / 22) * ferias_vencidas
    
    # === FORMATION ===
    # Valor por hora de formacao (estimativa: 10% do vencimento dia)
    valor_hora_formacao = (vencimento_base / 22) / 8  # 8 horas por dia
    formacao = valor_hora_formacao * horas_formacao
    
    # === ULTIMO MES ===
    ultimo_mes = valor_dia * dias_ultimo_mes
    
    # === TOTAL ===
    total = (compensacao_antiguidade + proporcional_natal + proporcional_ferias +
             ferias_nao_gozadas + formacao + ultimo_mes)
    
    return {
        "total": round(total, 2),
        "anos_trabalho": round(anos_trabalho, 1),
        "compensacao_antiguidade": round(compensacao_antiguidade, 2),
        "proporcional_natal": round(proporcional_natal, 2),
        "proporcional_ferias": round(proporcional_ferias, 2),
        "ferias_nao_gozadas": round(ferias_nao_gozadas, 2),
        "formacao": round(formacao, 2),
        "ultimo_mes": round(ultimo_mes, 2),
        "motivo": motivo
    }