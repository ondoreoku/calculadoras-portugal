"""Noticias.py - Gestao de Noticias via RSS com Cache SQLite."""

import feedparser
import sqlite3
from datetime import datetime, timedelta
import re

DATABASE = "database.db"

FEEDS_RSS = [
    "https://eco.sapo.pt/rss/",
    "https://www.jornaldenegocios.pt/rss/",
    "https://ojornaleconomico.pt/feed/",
]

PALAVRAS_CHAVE = [
    "salario", "salario", "irs", "imposto", "rendimento",
    "subsidio", "subsidio", "desemprego", "reforma", "pensao", "pensao",
    "seguranca social", "seguranca social", "trabalho", "emprego",
    "euribor", "credito", "credito", "habitacao", "habitacao",
    "hipoteca", "banco", "spread", "juro", "taxa", "financiamento",
    "inflacao", "inflacao", "economia", "financas", "financas",
    "pib", "deficit", "deficit", "orcamento", "orcamento",
    "ministerio", "ministerio", "governo", "bruxelas", "europa",
    "ias", "smn", "salario minimo", "salario minimo",
    "preco", "preco", "custo", "aumento", "descida",
]

MAX_NOTICIAS_POR_FEED = 15
MAX_NOTICIAS_HOME = 9
DIAS_CACHE_MAX = 7


def get_db():
    """Abre conexao com SQLite."""
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con


def formatar_data(data_raw):
    """Converte data RSS para formato legivel."""
    if not data_raw:
        return "Data desconhecida"
    formatos = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%d %b %Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formatos:
        try:
            data_obj = datetime.strptime(data_raw, fmt)
            return data_obj.strftime("%d %b %Y")
        except ValueError:
            continue
    return data_raw[:16] if len(data_raw) > 16 else data_raw


def fetch_rss_feed(url_feed):
    """Busca e parseia um feed RSS individual."""
    noticias = []
    try:
        feed = feedparser.parse(url_feed)
        for entry in feed.entries[:MAX_NOTICIAS_POR_FEED]:
            titulo = entry.get("title", "Sem titulo")
            resumo_raw = entry.get("summary", entry.get("description", ""))
            resumo_limpo = re.sub(r'<[^>]+>', '', resumo_raw)
            if len(resumo_limpo) > 200:
                resumo_limpo = resumo_limpo[:197] + "..."
            url = entry.get("link", "#")
            fonte_nome = feed.feed.get("title", "Desconhecida")
            if " - " in fonte_nome:
                fonte_nome = fonte_nome.split(" - ")[0]
            elif " | " in fonte_nome:
                fonte_nome = fonte_nome.split(" | ")[0]
            data_raw = entry.get("published", entry.get("updated", ""))
            data_formatada = formatar_data(data_raw)
            tags = entry.get("tags", [])
            if tags:
                categoria = tags[0].get("term", "Economia")
            else:
                categoria = "Economia"
            texto_para_busca = (titulo + " " + resumo_limpo).lower()
            e_relevante = any(palavra in texto_para_busca for palavra in PALAVRAS_CHAVE)
            if e_relevante:
                noticias.append({
                    "titulo": titulo,
                    "resumo": resumo_limpo,
                    "url": url,
                    "fonte": fonte_nome,
                    "data": data_formatada,
                    "categoria": categoria,
                })
    except Exception as e:
        print(f"[AVISO] Erro ao ler feed {url_feed}: {e}")
    return noticias


def atualizar_noticias():
    """Busca noticias de todos os feeds RSS e guarda no SQLite."""
    print("[INFO] A iniciar atualizacao de noticias via RSS...")
    todas_noticias = []
    for url in FEEDS_RSS:
        print(f"[INFO] A processar feed: {url}")
        noticias_feed = fetch_rss_feed(url)
        print(f"[INFO]  -> {len(noticias_feed)} noticias relevantes encontradas")
        todas_noticias.extend(noticias_feed)
    print(f"[INFO] Total de noticias relevantes: {len(todas_noticias)}")
    con = get_db()
    cur = con.cursor()
    noticias_inseridas = 0
    for noticia in todas_noticias:
        cur.execute("SELECT id FROM noticias WHERE url = ?", (noticia["url"],))
        resultado = cur.fetchone()
        if resultado is None:
            cur.execute("""
                INSERT INTO noticias (titulo, resumo, url, fonte, categoria, data_publicacao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                noticia["titulo"],
                noticia["resumo"],
                noticia["url"],
                noticia["fonte"],
                noticia["categoria"],
                noticia["data"]
            ))
            noticias_inseridas += 1
    con.commit()
    con.close()
    print(f"[OK] {noticias_inseridas} noticias novas inseridas")
    return noticias_inseridas


def get_noticias(limite=MAX_NOTICIAS_HOME):
    """
    Le noticias do SQLite para a home page.

    Garante que o numero de noticias e sempre multiplo de 3
    para o grid ficar equilibrado (3, 6, 9, 12...).
    Se nao houver noticias suficientes, preenche com backup.
    """
    con = get_db()
    cur = con.cursor()

    # Busca mais noticias do que o limite para ter margem
    cur.execute("""
        SELECT titulo, resumo, url, fonte, categoria, data_publicacao
        FROM noticias
        WHERE ativa = 1
        ORDER BY data_cache DESC
        LIMIT ?
    """, (limite,))

    rows = cur.fetchall()
    con.close()

    noticias = []
    for row in rows:
        noticias.append({
            "titulo": row["titulo"],
            "resumo": row["resumo"],
            "url": row["url"],
            "fonte": row["fonte"],
            "categoria": row["categoria"],
            "data": row["data_publicacao"],
        })

    # Se nao houver noticias suficientes, preenche com backup
    if len(noticias) < limite:
        print(f"[AVISO] Apenas {len(noticias)} noticias em cache. A preencher com backup.")
        backup = get_noticias_backup()

        # Adiciona noticias de backup ate atingir o limite
        for b in backup:
            if len(noticias) >= limite:
                break
            # Verifica se ja nao existe esta noticia (evita duplicados)
            urls_existentes = [n["url"] for n in noticias]
            if b["url"] not in urls_existentes:
                noticias.append(b)

    # Garante multiplo de 3: se temos 5, cortamos para 3; se temos 7, cortamos para 6
    resto = len(noticias) % 3
    if resto != 0:
        noticias = noticias[:-resto]

    return noticias


def get_noticias_backup():
    """Noticias estaticas de fallback. Agora com 9 noticias."""
    return [
        {
            "titulo": "IAS 2026 atualizado",
            "resumo": "O Indexante dos Apoios Sociais mantem-se em 510 euros, afetando calculos de subsidio e outros apoios sociais em Portugal.",
            "url": "https://www.seg-social.pt",
            "fonte": "Seguranca Social",
            "categoria": "Trabalho",
            "data": "15 Jul 2026"
        },
        {
            "titulo": "Novas taxas IRS para 2026",
            "resumo": "Tabelas de retencao na fonte atualizadas para o segundo semestre de 2026. Consulta as novas taxas aplicaveis ao teu salario.",
            "url": "https://www.portaldasfinancas.gov.pt",
            "fonte": "Portal das Financas",
            "categoria": "Impostos",
            "data": "10 Jul 2026"
        },
        {
            "titulo": "Euribor em queda continua",
            "resumo": "Taxas de juro para credito habitacao continuam a descer, beneficiando novos contratos e revisoes de taxas variaveis.",
            "url": "https://www.bportugal.pt",
            "fonte": "Banco de Portugal",
            "categoria": "Habitacao",
            "data": "05 Jul 2026"
        },
        {
            "titulo": "Reforma antecipada mantem requisitos",
            "resumo": "Os criterios para a reforma antecipada nao sofrem alteracoes em 2026. Idade e descontos continuam a ser os fatores determinantes.",
            "url": "https://www.seg-social.pt",
            "fonte": "Seguranca Social",
            "categoria": "Reforma",
            "data": "12 Jul 2026"
        },
        {
            "titulo": "Salario minimo nacional em discussao",
            "resumo": "Governo e parceiros sociais discutem novo aumento do salario minimo para o segundo semestre de 2026.",
            "url": "https://www.portugal.gov.pt",
            "fonte": "Governo de Portugal",
            "categoria": "Trabalho",
            "data": "08 Jul 2026"
        },
        {
            "titulo": "Inflacao estabiliza em 2,1%",
            "resumo": "Indice de precos no consumidor mantem tendencia de desaceleracao, com impacto positivo no poder de compra das familias.",
            "url": "https://www.ine.pt",
            "fonte": "INE",
            "categoria": "Economia",
            "data": "03 Jul 2026"
        },
        {
            "titulo": "Spread bancario em analise",
            "resumo": "Banco de Portugal monitoriza margens dos bancos na concessao de credito habitacao. Novas medidas podem ser anunciadas.",
            "url": "https://www.bportugal.pt",
            "fonte": "Banco de Portugal",
            "categoria": "Habitacao",
            "data": "01 Jul 2026"
        },
        {
            "titulo": "Subsidio de ferias: regras 2026",
            "resumo": "Trabalhadores independentes podem solicitar subsidio de ferias desde que cumpram requisitos de descontos. Saiba como funciona.",
            "url": "https://www.seg-social.pt",
            "fonte": "Seguranca Social",
            "categoria": "Trabalho",
            "data": "28 Jun 2026"
        },
        {
            "titulo": "Descontos para a SS: guia pratico",
            "resumo": "Como calcular os descontos para a Seguranca Social em 2026. Taxas aplicaveis a trabalhadores por conta de outrem e independentes.",
            "url": "https://www.seg-social.pt",
            "fonte": "Seguranca Social",
            "categoria": "Trabalho",
            "data": "25 Jun 2026"
        },
    ]


def limpar_cache_antigo():
    """Remove noticias com mais de DIAS_CACHE_MAX dias."""
    con = get_db()
    cur = con.cursor()
    data_limite = datetime.now() - timedelta(days=DIAS_CACHE_MAX)
    data_limite_str = data_limite.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        DELETE FROM noticias
        WHERE data_cache < ?
    """, (data_limite_str,))
    noticias_removidas = cur.rowcount
    con.commit()
    con.close()
    if noticias_removidas > 0:
        print(f"[INFO] {noticias_removidas} noticias antigas removidas")
    return noticias_removidas


if __name__ == "__main__":
    print("=" * 60)
    print("  TESTE DO MODULO NOTICIAS.PY")
    print("=" * 60)
    inseridas = atualizar_noticias()
    print(f"Noticias inseridas: {inseridas}")
    noticias = get_noticias(limite=9)
    print(f"Noticias lidas: {len(noticias)}")
    for n in noticias:
        print(f"  -> {n['fonte']}: {n['titulo'][:50]}...")
    removidas = limpar_cache_antigo()
    print(f"Noticias removidas: {removidas}")
