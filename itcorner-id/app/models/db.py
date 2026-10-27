import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    """
    Membuka koneksi ke PostgreSQL menggunakan konfigurasi Environment Variables.
    """
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "itcorner_db"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgrespassword"),
        cursor_factory=RealDictCursor,
    )
    return conn


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Helper eksekusi query menggunakan Parameterized Query (%s)`
    untuk mencegah celah keamanan SQL Injection (SQLi).
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            result = None
            if fetch_one:
                result = cur.fetchone()
            elif fetch_all:
                result = cur.fetchall()
            if commit:
                conn.commit()
            return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()