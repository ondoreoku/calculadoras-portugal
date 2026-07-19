"""
INITDB.PY — Inicialização da Base de Dados (SQLite e PostgreSQL)
"""
from utils.db import get_connection, get_cursor

def create_tables():
    """Cria as tabelas na base de dados ativa."""
    conn, eh_postgres = get_connection()
    cur = get_cursor(conn, eh_postgres)

    # Sintaxe diferente para AUTOINCREMENT / SERIAL
    id_type = "SERIAL PRIMARY KEY" if eh_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    timestamp_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if eh_postgres else "DATETIME DEFAULT CURRENT_TIMESTAMP"

    # 1. Tabela Noticias
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS noticias (
            id {id_type},
            titulo TEXT NOT NULL,
            resumo TEXT,
            url TEXT NOT NULL UNIQUE,
            fonte TEXT,
            categoria TEXT,
            data_publicacao TEXT,
            data_cache {timestamp_type},
            ativa INTEGER DEFAULT 1
        )
    """)

    # 2. Tabela Historico
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS historico_calculos (
            id {id_type},
            tipo TEXT NOT NULL,
            input_json TEXT,
            resultado_json TEXT,
            data_hora {timestamp_type}
        )
    """)

    # 3. Tabela Taxas
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS taxas_atualizaveis (
            id {id_type},
            nome TEXT NOT NULL,
            valor REAL,
            ano INTEGER,
            descricao TEXT,
            data_atualizacao {timestamp_type}
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("[OK] Tabelas criadas/atualizadas com sucesso.")

def seed_taxas():
    """Insere taxas iniciais se não existirem."""
    conn, eh_postgres = get_connection()
    cur = get_cursor(conn, eh_postgres)

    taxas_iniciais = [
        ("IAS_2026", 510.00, 2026, "Indexante dos Apoios Sociais 2026"),
        ("IAS_MINIMO_SUBSIDIO", 510.00, 2026, "Valor mínimo do subsídio de desemprego"),
        ("IAS_MAXIMO_SUBSIDIO", 1275.00, 2026, "Valor máximo do subsídio de desemprego"),
    ]

    for nome, valor, ano, descricao in taxas_iniciais:
        # Verifica se já existe
        cur.execute("SELECT id FROM taxas_atualizaveis WHERE nome = %s AND ano = %s" if eh_postgres else "SELECT id FROM taxas_atualizaveis WHERE nome = ? AND ano = ?", 
                    (nome, ano))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO taxas_atualizaveis (nome, valor, ano, descricao) VALUES (%s, %s, %s, %s)" if eh_postgres else "INSERT INTO taxas_atualizaveis (nome, valor, ano, descricao) VALUES (?, ?, ?, ?)",
                (nome, valor, ano, descricao)
            )
            
    conn.commit()
    cur.close()
    conn.close()
    print("[OK] Taxas iniciais inseridas.")

if __name__ == "__main__":
    print("=" * 60)
    print("  INICIALIZAÇÃO DA BASE DE DADOS")
    print("=" * 60)
    create_tables()
    seed_taxas()
    print("Base de dados pronta!")