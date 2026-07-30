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
