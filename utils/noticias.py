"""Noticias.py - Gestao de Noticias via RSS com Cache (SQLite/Postgres)."""
import feedparser
import re
from datetime import datetime, timedelta
from utils.db import get_connection, get_cursor

FEEDS_RSS = [
    "https://eco.sapo.pt/rss/",
    "https://www.jornaldenegocios.pt/rss/",
    "https://ojornaleconomico.pt/feed/",
]

# Lista restrita para evitar notícias irrelevantes
PALAVRAS_CHAVE = [
    "salario liquido", "salario bruto", "salario minimo", 
    "irs ", "retenção irs", "tabelas irs", "escalões irs",
    "subsidio desemprego", "subsidio ferias", "subsidio natal",
    "segurança social", "reforma ", "pensão ",
    "rescisão contrato", "indemnização", "lay-off",
    "credito habitação", "euribor ", "spread bancario", "taxa esforço",
    "ias 2026", "indexante apoios", "inflacao portugal"
]

MAX_NOTICIAS_POR_FEED = 15
MAX_NOTICIAS_HOME = 9
DIAS_CACHE_MAX = 7

def formatar_data(data_raw):
    if not data_raw: return "Data desconhecida"
    formatos = [
        "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ",
        "%d %b %Y %H:%M:%S", "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formatos:
        try:
            data_obj = datetime.strptime(data_raw, fmt)
            return data_obj.strftime("%d %b %Y")
        except ValueError:
            continue
    return data_raw[:16] if len(data_raw) > 16 else data_raw

def fetch_rss_feed(url_feed):
    noticias = []
    try:
        feed = feedparser.parse(url_feed)
        for entry in feed.entries[:MAX_NOTICIAS_POR_FEED]:
            titulo = entry.get("title", "Sem titulo")
            resumo_raw = entry.get("summary", entry.get("description", ""))
            resumo_limpo = re.sub(r'<[^>]+>', '', resumo_raw)
            if len(resumo_limpo) > 200: resumo_limpo = resumo_limpo[:197] + "..."
            url = entry.get("link", "#")
            fonte_nome = feed.feed.get("title", "Desconhecida")
            if " - " in fonte_nome: fonte_nome = fonte_nome.split(" - ")[0]
            elif " | " in fonte_nome: fonte_nome = fonte_nome.split(" | ")[0]
            
            data_raw = entry.get("published", entry.get("updated", ""))
            data_formatada = formatar_data(data_raw)
            tags = entry.get("tags", [])
            categoria = tags[0].get("term", "Economia") if tags else "Economia"
            
            texto_para_busca = (titulo + " " + resumo_limpo).lower()
            e_relevante = any(palavra in texto_para_busca for palavra in PALAVRAS_CHAVE)
            
            if e_relevante:
                noticias.append({
                    "titulo": titulo, "resumo": resumo_limpo, "url": url,
                    "fonte": fonte_nome, "data": data_formatada, "categoria": categoria,
                })
    except Exception as e:
        print(f"[AVISO] Erro ao ler feed {url_feed}: {e}")
    return noticias

def atualizar_noticias():
    print("[INFO] A iniciar atualizacao de noticias via RSS...")
    todas_noticias = []
    for url in FEEDS_RSS:
        noticias_feed = fetch_rss_feed(url)
        todas_noticias.extend(noticias_feed)
    
    conn, eh_postgres = get_connection()
    cur = get_cursor(conn, eh_postgres)
    noticias_inseridas = 0
    
    for noticia in todas_noticias:
        # Verifica se já existe (funciona em SQLite e Postgres)
        if eh_postgres:
            cur.execute("SELECT id FROM noticias WHERE url = %s", (noticia["url"],))
        else:
            cur.execute("SELECT id FROM noticias WHERE url = ?", (noticia["url"],))
            
        if not cur.fetchone():
            if eh_postgres:
                cur.execute("""
                    INSERT INTO noticias (titulo, resumo, url, fonte, categoria, data_publicacao)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (noticia["titulo"], noticia["resumo"], noticia["url"], noticia["fonte"], noticia["categoria"], noticia["data"]))
            else:
                cur.execute("""
                    INSERT INTO noticias (titulo, resumo, url, fonte, categoria, data_publicacao)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (noticia["titulo"], noticia["resumo"], noticia["url"], noticia["fonte"], noticia["categoria"], noticia["data"]))
            noticias_inseridas += 1
            
    conn.commit()
    cur.close()
    conn.close()
    print(f"[OK] {noticias_inseridas} noticias novas inseridas")
    return noticias_inseridas

def get_noticias(limite=MAX_NOTICIAS_HOME):
    conn, eh_postgres = get_connection()
    cur = get_cursor(conn, eh_postgres)
    
    if eh_postgres:
        cur.execute("SELECT titulo, resumo, url, fonte, categoria, data_publicacao FROM noticias WHERE ativa = 1 ORDER BY data_cache DESC LIMIT %s", (limite,))
    else:
        cur.execute("SELECT titulo, resumo, url, fonte, categoria, data_publicacao FROM noticias WHERE ativa = 1 ORDER BY data_cache DESC LIMIT ?", (limite,))
        
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    noticias = [{"titulo": r["titulo"], "resumo": r["resumo"], "url": r["url"], "fonte": r["fonte"], "categoria": r["categoria"], "data": r["data_publicacao"]} for r in rows]
    
    if len(noticias) < limite:
        backup = get_noticias_backup()
        urls_existentes = [n["url"] for n in noticias]
        for b in backup:
            if len(noticias) >= limite: break
            if b["url"] not in urls_existentes: noticias.append(b)
            
    resto = len(noticias) % 3
    if resto != 0: noticias = noticias[:-resto]
    return noticias

def get_noticias_backup():
    return [
        {"titulo": "IAS 2026 atualizado", "resumo": "O Indexante dos Apoios Sociais mantem-se em 510 euros.", "url": "https://www.seg-social.pt", "fonte": "Seguranca Social", "categoria": "Trabalho", "data": "15 Jul 2026"},
        {"titulo": "Novas taxas IRS para 2026", "resumo": "Tabelas de retencao na fonte atualizadas.", "url": "https://www.portaldasfinancas.gov.pt", "fonte": "Financas", "categoria": "Impostos", "data": "10 Jul 2026"},
        {"titulo": "Euribor em queda continua", "resumo": "Taxas de juro para credito habitacao continuam a descer.", "url": "https://www.bportugal.pt", "fonte": "Banco de Portugal", "categoria": "Habitacao", "data": "05 Jul 2026"},
    ]

def limpar_cache_antigo():
    conn, eh_postgres = get_connection()
    cur = get_cursor(conn, eh_postgres)
    data_limite = datetime.now() - timedelta(days=DIAS_CACHE_MAX)
    data_limite_str = data_limite.strftime("%Y-%m-%d %H:%M:%S")
    
    if eh_postgres:
        cur.execute("DELETE FROM noticias WHERE data_cache < %s", (data_limite_str,))
    else:
        cur.execute("DELETE FROM noticias WHERE data_cache < ?", (data_limite_str,))
        
    removidas = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return removidas