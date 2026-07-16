"""
SALARIO.PY - Calculadora de Salario Liquido
"""

def calcular_salario(bruto, regime="outrem", subsidio_alimentacao=6.0, 
                     estado_civil="solteiro", coeficiente_atividade=0.75,
                     retencao_irs=0.15, isento_ss="nao"):
    """
    Calcula o salario liquido.
    
    Regime 'outrem': conta de outrem (SS 11%, IRS progressivo)
    Regime 'eni': trabalhador independente
    """
    
    if regime == "outrem":
        # Seguranca Social: 11% do bruto
        ss = bruto * 0.11
        
        # IRS progressivo simplificado (tabelas 2026 aproximadas)
        rendimento_anual = bruto * 14  # 14 meses (inclui subsidios)
        
        if rendimento_anual <= 7703:
            taxa_irs = 0.0
        elif rendimento_anual <= 11623:
            taxa_irs = 0.145
        elif rendimento_anual <= 16472:
            taxa_irs = 0.23
        elif rendimento_anual <= 21321:
            taxa_irs = 0.28
        elif rendimento_anual <= 27146:
            taxa_irs = 0.35
        elif rendimento_anual <= 39791:
            taxa_irs = 0.37
        elif rendimento_anual <= 51997:
            taxa_irs = 0.45
        elif rendimento_anual <= 75709:
            taxa_irs = 0.465
        else:
            taxa_irs = 0.48
        
        # Deducao especifica dependente (simplificado)
        if estado_civil == "casado":
            taxa_irs = max(0, taxa_irs - 0.02)
        
        irs = bruto * taxa_irs
        
        # Subsidio alimentacao (isento ate certo limite, simplificado)
        subsidio_alim_mensal = subsidio_alimentacao * 22  # 22 dias uteis
        
        liquido = bruto - ss - irs + subsidio_alim_mensal
        
        return {
            "bruto": round(bruto, 2),
            "seguranca_social": round(ss, 2),
            "irs": round(irs, 2),
            "subsidio_alimentacao": round(subsidio_alim_mensal, 2),
            "liquido": round(liquido, 2),
            "taxa_efetiva_irs": round(taxa_irs * 100, 2),
            "regime": "Conta de Outrem"
        }
    
    else:  # regime == "eni"
        # Trabalhador Independente (ENI)
        # Rendimento tributavel = bruto * coeficiente de atividade
        rendimento_tributavel = bruto * coeficiente_atividade
        
        # IRS retido na fonte
        irs = rendimento_tributavel * retencao_irs
        
        # SS: 21.4% sobre 70% do rendimento (se nao isento)
        if isento_ss == "nao":
            ss = (bruto * 0.70) * 0.214
        else:
            ss = 0
        
        liquido = bruto - irs - ss
        
        return {
            "bruto": round(bruto, 2),
            "rendimento_tributavel": round(rendimento_tributavel, 2),
            "irs": round(irs, 2),
            "seguranca_social": round(ss, 2),
            "liquido": round(liquido, 2),
            "coeficiente": coeficiente_atividade,
            "regime": "Trabalhador Independente (ENI)"
        }