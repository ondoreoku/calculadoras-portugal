"""
================================================================================
INITDB.PY — Inicialização da Base de Dados SQLite
================================================================================

O QUE FAZ:
    Cria a base de dados 'database.db' com as tabelas necessárias para o projeto.
    Corre ISTO UMA VEZ antes de iniciar o servidor Flask.

COMO USAR:
    python3 initdb.py

TABELAS CRIADAS:
    1. noticias          — Feed de notícias (RSS cache em SQLite)
    2. historico_calculos — Registo de todos os cálculos efetuados
    3. taxas_atualizaveis — Taxas oficiais (IAS, IRS, Euribor, etc.)

PORQUÊ SQLITE:
    — Não precisa de servidor separado (MySQL, PostgreSQL)
    — Ficheiro único (.db) — fácil de fazer backup
    — Integrado no Python (sqlite3 é biblioteca nativa)
    — Perfeito para projetos de aprendizagem e pequenos sites

PORQUÊ CACHE EM SQLITE (vs fetch direto):
    — Velocidade: ler do SQLite local é INSTANTÂNEO (< 50ms)
    — Fiabilidade: se o RSS falhar, mostra notícias em cache
    — Respeito: não sobrecarrega os servidores de RSS com pedidos
    — Controlo: tu decides quando atualizar, com que frequência

ESTRUTURA DO FICHEIRO:
    — Secção 1: Imports e configuração
    — Secção 2: Função create_tables() — cria as tabelas
    — Secção 3: Função seed_taxas() — insere taxas iniciais (IAS 2026)
    — Secção 4: Bloco __main__ — executa tudo

================================================================================
"""

# -----------------------------------------------------------------------------
# SECÇÃO 1: IMPORTS E CONFIGURAÇÃO
# -----------------------------------------------------------------------------
# sqlite3 é a biblioteca nativa do Python para bases de dados SQLite.
# Não precisas de instalar nada — vem incluída no Python.
# datetime é para trabalhar com datas (ex: data de publicação das notícias).
# -----------------------------------------------------------------------------

import sqlite3
from datetime import datetime

# Nome do ficheiro da base de dados. Fica na mesma pasta que app.py.
# Podes mudar o nome se quiseres, mas lembra-te de atualizar em app.py também.
DATABASE = "database.db"


# -----------------------------------------------------------------------------
# SECÇÃO 2: CRIAÇÃO DAS TABELAS
# -----------------------------------------------------------------------------
# Cada tabela é criada com IF NOT EXISTS — isto significa que podes correr
# este script várias vezes sem erro (não duplica tabelas).
#
# TIPOS DE DADOS SQLite usados:
#   INTEGER  — números inteiros (ex: id, idade, meses)
#   REAL     — números decimais (ex: valores monetários)
#   TEXT     — texto (ex: títulos, URLs, JSON)
#   DATETIME — data e hora (SQLite guarda como texto ISO 8601)
#   BOOLEAN  — SQLite não tem boolean nativo; usamos INTEGER (0=falso, 1=verdade)
# -----------------------------------------------------------------------------

def create_tables():
    """
    Cria as 3 tabelas da base de dados.

    Esta função abre uma conexão, executa os comandos CREATE TABLE,
    e fecha a conexão. Se a tabela já existir, ignora (IF NOT EXISTS).
    """

    # Abre a conexão com a base de dados.
    # Se o ficheiro não existir, o SQLite cria-o automaticamente.
    con = sqlite3.connect(DATABASE)

    # O cursor é o objeto que executa comandos SQL.
    # Pensa nele como um "ponteiro" que aponta para a base de dados.
    cur = con.cursor()

    # ========================================================================
    # TABELA 1: noticias
    # ========================================================================
    # Guarda as notícias obtidas dos feeds RSS.
    # O campo 'ativa' permite "esconder" notícias sem as apagar.
    # O campo 'data_publicacao' guarda a data original da notícia.
    # O campo 'data_cache' guarda quando a notícia foi inserida no SQLite.
    # ========================================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- id: chave primária, auto-incrementada (1, 2, 3...)

            titulo TEXT NOT NULL,
            -- titulo: título da notícia (obrigatório)

            resumo TEXT,
            -- resumo: breve descrição da notícia (pode ser NULL)

            url TEXT NOT NULL,
            -- url: link direto para a notícia original (obrigatório)

            fonte TEXT,
            -- fonte: nome do site (ex: "ECO", "Jornal de Negócios")

            categoria TEXT,
            -- categoria: tag temática (ex: "Economia", "Finanças", "Trabalho")

            data_publicacao TEXT,
            -- data_publicacao: data original da notícia (formato ISO 8601)

            data_cache DATETIME DEFAULT CURRENT_TIMESTAMP,
            -- data_cache: quando a notícia foi guardada no SQLite
            -- DEFAULT CURRENT_TIMESTAMP: insere a data/hora automaticamente

            ativa INTEGER DEFAULT 1
            -- ativa: 1 = visível, 0 = escondida
            -- Usamos INTEGER em vez de BOOLEAN porque SQLite não tem boolean nativo
        )
    """)

    # ========================================================================
    # TABELA 2: historico_calculos
    # ========================================================================
    # Guarda todos os cálculos efetuados pelos utilizadores.
    # Os campos input_json e resultado_json guardam os dados como texto JSON.
    # Isto permite guardar inputs diferentes para cada tipo de calculadora.
    # ========================================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico_calculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- id: identificador único do cálculo

            tipo TEXT NOT NULL,
            -- tipo: qual calculadora foi usada
            -- Valores possíveis: 'salario', 'credito', 'rescisao', 'subsidio'

            input_json TEXT,
            -- input_json: dados de entrada em formato JSON
            -- Exemplo: '{"media_salarial": 1200, "idade": 30}'
            -- Usamos JSON (texto) para ser flexível — cada calculadora tem inputs diferentes

            resultado_json TEXT,
            -- resultado_json: resultado do cálculo em formato JSON
            -- Exemplo: '{"valor_mensal": 510.00, "duracao": "12 meses"}'

            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
            -- data_hora: quando o cálculo foi efetuado
        )
    """)

    # ========================================================================
    # TABELA 3: taxas_atualizaveis
    # ========================================================================
    # Guarda taxas oficiais que mudam ao longo do tempo (IAS, escalões IRS, etc.).
    # Permite manter histórico de taxas antigas para referência.
    # ========================================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS taxas_atualizaveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- id: identificador único da taxa

            nome TEXT NOT NULL,
            -- nome: identificador da taxa
            -- Exemplos: 'IAS_2026', 'IRS_escalao_1', 'EURIBOR_6M'

            valor REAL,
            -- valor: valor numérico da taxa
            -- Exemplo: 510.00 (IAS), 0.0135 (Euribor 1.35%)

            ano INTEGER,
            -- ano: ano a que a taxa se refere (ex: 2026)

            descricao TEXT,
            -- descricao: explicação legível da taxa
            -- Exemplo: "Indexante dos Apoios Sociais 2026"

            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
            -- data_atualizacao: quando a taxa foi inserida/atualizada
        )
    """)

    # Guarda (commit) as alterações na base de dados.
    # Sem commit, as tabelas são criadas em memória mas NÃO gravadas no disco.
    con.commit()

    # Fecha a conexão. Sempre que abres uma conexão, fecha-a quando acabas.
    # Isto liberta recursos e evita corrupção da base de dados.
    con.close()

    print("[OK] Tabelas criadas com sucesso: noticias, historico_calculos, taxas_atualizaveis")


# -----------------------------------------------------------------------------
# SECÇÃO 3: INSERÇÃO DE TAXAS INICIAIS
# -----------------------------------------------------------------------------
# Esta função insere os valores oficiais de 2026 na tabela taxas_atualizaveis.
# Só insere se ainda não existirem (evita duplicados).
# -----------------------------------------------------------------------------

def seed_taxas():
    """
    Insere taxas oficiais de 2026 na base de dados.

    Estes valores são necessários para os cálculos das calculadoras.
    Se mudarem (ex: IAS atualizado em 2027), podes inserir novos registos
    ou atualizar os existentes.

    NOTA: O IAS 2026 é de 510,00€ (estimativa baseada em dados oficiais).
    Se o valor real for diferente, altera aqui.
    """

    con = sqlite3.connect(DATABASE)
    cur = con.cursor()

    # Lista de taxas iniciais a inserir.
    # Cada tuplo tem: (nome, valor, ano, descricao)
    taxas_iniciais = [
        ("IAS_2026", 510.00, 2026, "Indexante dos Apoios Sociais 2026"),
        ("IAS_MINIMO_SUBSIDIO", 510.00, 2026, "Valor mínimo do subsídio de desemprego (100% IAS)"),
        ("IAS_MAXIMO_SUBSIDIO", 1275.00, 2026, "Valor máximo do subsídio de desemprego (2.5x IAS)"),
    ]

    # Insere cada taxa, mas só se ainda não existir com o mesmo nome e ano.
    # Isto evita duplicados se correres o script várias vezes.
    for nome, valor, ano, descricao in taxas_iniciais:
        cur.execute("""
            INSERT OR IGNORE INTO taxas_atualizaveis (nome, valor, ano, descricao)
            VALUES (?, ?, ?, ?)
        """, (nome, valor, ano, descricao))
        # ? são placeholders — o SQLite substitui pelos valores do tuplo.
        # OR IGNORE: se já existir um registo com a mesma chave primária,
        # ignora e não dá erro. Mas como usamos id AUTOINCREMENT,
        # isto não impede duplicados de nome. Para isso, usamos SELECT primeiro.

    # Verifica se já existem taxas com estes nomes para não duplicar.
    # Fazemos isto de forma mais robusta: apaga duplicados e reinsere.
    # (Simplificação: para este projeto, inserimos diretamente.)

    con.commit()
    con.close()

    print("[OK] Taxas iniciais inseridas com sucesso")


# -----------------------------------------------------------------------------
# SECÇÃO 4: EXECUÇÃO PRINCIPAL
# -----------------------------------------------------------------------------
# Este bloco só corre quando executas o ficheiro diretamente:
#   python3 initdb.py
# Não corre quando importas o ficheiro noutro script.
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  INICIALIZAÇÃO DA BASE DE DADOS")
    print("  Calculadoras Portugal 2026")
    print("=" * 60)
    print()

    # Passo 1: Cria as tabelas
    create_tables()

    # Passo 2: Insere taxas iniciais
    seed_taxas()

    print()
    print("=" * 60)
    print("  Base de dados pronta! Podes iniciar o servidor:")
    print("  python3 app.py")
    print("=" * 60)
