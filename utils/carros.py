import requests
import json

def calcular_isv(co2, cilindrada, ano):
    url = f"https://claracars.pt/api/public/isv?co2={co2}&cc={cilindrada}&year={ano}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"erro": f"Erro ao calcular ISV (status: {response.status_code})"}
    except Exception as e:
        return {"erro": f"API indisponível: {str(e)}"}

def calcular_iuc(co2, ano):
    url = f"https://claracars.pt/api/public/iuc?co2={co2}&year={ano}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"erro": f"Erro ao calcular IUC (status: {response.status_code})"}
    except Exception as e:
        return {"erro": f"API indisponível: {str(e)}"}

# Fallback para IUC quando a API externa falha
def calcular_iuc_fallback(co2, ano):
    """
    Calcula IUC com base em valores aproximados
    """
    # Valores base aproximados para 2026
    if co2 <= 100:
        base = 50
    elif co2 <= 140:
        base = 100
    elif co2 <= 180:
        base = 150
    elif co2 <= 250:
        base = 200
    else:
        base = 300
    
    # Fator de antiguidade (carros mais antigos pagam menos)
    idade = 2026 - ano
    if idade > 10:
        fator = 0.5
    elif idade > 5:
        fator = 0.7
    else:
        fator = 1.0
    
    return {
        "iuc": round(base * fator, 2),
        "co2": co2,
        "ano": ano,
        "base": base,
        "fator": fator,
        "nota": "Valor estimado (API externa indisponível)"
    }

def calcular_iuc_fallback(co2, ano):
    """
    Calcula IUC com base em valores aproximados (fallback)
    """
    # Valores base aproximados para 2026
    if co2 <= 100:
        base = 50
    elif co2 <= 140:
        base = 100
    elif co2 <= 180:
        base = 150
    elif co2 <= 250:
        base = 200
    else:
        base = 300
    
    # Fator de antiguidade (carros mais antigos pagam menos)
    idade = 2026 - ano
    if idade > 10:
        fator = 0.5
    elif idade > 5:
        fator = 0.7
    else:
        fator = 1.0
    
    return {
        "iuc": round(base * fator, 2),
        "co2": co2,
        "ano": ano,
        "base": base,
        "fator": fator,
        "nota": "Valor estimado (API externa indisponível)"
    }

def calcular_iuc_fallback(co2, ano):
    """
    Calcula IUC com base em valores aproximados (fallback quando API externa falha)
    """
    # Valores base aproximados para 2026
    if co2 <= 100:
        base = 50
    elif co2 <= 140:
        base = 100
    elif co2 <= 180:
        base = 150
    elif co2 <= 250:
        base = 200
    else:
        base = 300
    
    # Fator de antiguidade (carros mais antigos pagam menos)
    idade = 2026 - ano
    if idade > 10:
        fator = 0.5
    elif idade > 5:
        fator = 0.7
    else:
        fator = 1.0
    
    return {
        "iuc": round(base * fator, 2),
        "co2": co2,
        "ano": ano,
        "base": base,
        "fator": fator,
        "nota": "Valor estimado (API externa indisponível)"
    }
