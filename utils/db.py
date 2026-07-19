"""
db.py - Adaptador de Base de Dados (SQLite e PostgreSQL)
Permite que a app funcione localmente com SQLite e no Render com PostgreSQL.
"""
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    """
    Retorna uma tuplo: (conexao, eh_postgres)
    - Se existir DATABASE_URL (Render), usa PostgreSQL.
    - Se não existir (Local), usa SQLite.
    """
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        # Render usa 'postgres://', mas o psycopg2 quer 'postgresql://'
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        conn = psycopg2.connect(database_url)
        return conn, True  # True = é PostgreSQL
    else:
        # Local: SQLite
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row  # Permite aceder por nome: row["titulo"]
        return conn, False  # False = é SQLite

def get_cursor(conn, eh_postgres):
    """Retorna o cursor correto dependendo da base de dados."""
    if eh_postgres:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()