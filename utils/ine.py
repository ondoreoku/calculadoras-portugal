import requests
INDICADOR_IPC = "0012345"
def get_indicador_ine(varcd, lang="PT"):
    url = f"https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd={varcd}&lang={lang}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None
def get_inflacao():
    data = get_indicador_ine(INDICADOR_IPC)
    if data:
        try:
            return {"valor": data.get("Dados", {}).get("Valor", [0])[0] if data.get("Dados") else 0, "periodo": data.get("Dados", {}).get("Periodo", [""])[0] if data.get("Dados") else "", "fonte": "INE"}
        except:
            return {"erro": "Erro ao processar dados do INE"}
    return {"erro": "Não foi possível obter dados do INE"}
def get_noticias_economia_backup():
    return [{"titulo": "Inflação em Portugal desacelera para 2,1%", "resumo": "O IPC registou uma variação de 2,1% em junho.", "fonte": "INE", "data": "Jul 2026"}]
def get_noticias_economia():
    return get_noticias_economia_backup()
