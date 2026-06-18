import psycopg2
import psycopg2.extras
import streamlit as st

def get_conn():
    return psycopg2.connect(
        st.secrets["SUPABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def init_db():
    schema = open("schema.sql").read()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(schema)
        conn.commit()

# ── Item ──────────────────────────────────────
def get_items(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM item ORDER BY id")
        return cur.fetchall()

def update_stok(conn, id_item, stok):
    with conn.cursor() as cur:
        cur.execute("UPDATE item SET stok=%s WHERE id=%s", (stok, id_item))
    conn.commit()

def update_tipe(conn, id_item, tipe):
    with conn.cursor() as cur:
        cur.execute("UPDATE item SET tipe=%s WHERE id=%s", (tipe, id_item))
    conn.commit()

# ── Lantai ────────────────────────────────────
def get_lantai(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM lantai ORDER BY id")
        return cur.fetchall()

# ── Sesi ──────────────────────────────────────
def get_sesi(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM sesi ORDER BY id")
        return cur.fetchall()

# ── Distribusi ────────────────────────────────
def upsert_distribusi(conn, id_lantai, id_item, jumlah):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO distribusi (id_lantai, id_item, jumlah)
            VALUES (%s, %s, %s)
            ON CONFLICT (id_lantai, id_item) DO UPDATE SET jumlah = EXCLUDED.jumlah
        """, (id_lantai, id_item, jumlah))
    conn.commit()

def get_distribusi(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT d.*, l.nama as nama_lantai, i.nama as nama_item
            FROM distribusi d
            JOIN lantai l ON d.id_lantai = l.id
            JOIN item   i ON d.id_item   = i.id
            ORDER BY d.id_lantai, d.id_item
        """)
        return cur.fetchall()

# ── Transaksi ─────────────────────────────────
def add_transaksi(conn, hari, id_sesi, id_lantai, id_item, jumlah, catatan=""):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transaksi (hari, id_sesi, id_lantai, id_item, jumlah, catatan)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (hari, id_sesi, id_lantai, id_item, jumlah, catatan))
    conn.commit()

def delete_transaksi(conn, trx_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM transaksi WHERE id=%s", (trx_id,))
    conn.commit()

def get_transaksi(conn, hari=None, id_lantai=None):
    q = """
        SELECT t.*, s.jam, s.nama as nama_sesi,
               l.nama as nama_lantai, i.nama as nama_item
        FROM transaksi t
        JOIN sesi   s ON t.id_sesi   = s.id
        JOIN lantai l ON t.id_lantai = l.id
        JOIN item   i ON t.id_item   = i.id
        WHERE 1=1
    """
    params = []
    if hari:
        q += " AND t.hari=%s"; params.append(hari)
    if id_lantai:
        q += " AND t.id_lantai=%s"; params.append(id_lantai)
    q += " ORDER BY t.hari, s.jam, t.created_at"
    with conn.cursor() as cur:
        cur.execute(q, params)
        return cur.fetchall()

def get_saldo_per_item(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                i.id, i.nama, i.stok, i.tipe,
                COALESCE(d.total_dist, 0)  AS total_distribusi,
                COALESCE(tx.net, 0)        AS net_transaksi,
                i.stok
                    - COALESCE(d.total_dist, 0)
                    - COALESCE(tx.net, 0)  AS saldo_gudang,
                COALESCE(d.total_dist, 0)
                    + COALESCE(tx.net, 0)  AS total_keluar
            FROM item i
            LEFT JOIN (
                SELECT id_item, SUM(jumlah) AS total_dist
                FROM distribusi GROUP BY id_item
            ) d ON i.id = d.id_item
            LEFT JOIN (
                SELECT id_item, SUM(jumlah) AS net
                FROM transaksi GROUP BY id_item
            ) tx ON i.id = tx.id_item
            ORDER BY i.id
        """)
        return cur.fetchall()

def get_barang_belum_kembali(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                i.id, i.nama,
                COALESCE(d.total_dist, 0) + COALESCE(tx.net, 0) AS total_di_luar
            FROM item i
            LEFT JOIN (
                SELECT id_item, SUM(jumlah) AS total_dist
                FROM distribusi GROUP BY id_item
            ) d ON i.id = d.id_item
            LEFT JOIN (
                SELECT id_item, SUM(jumlah) AS net
                FROM transaksi GROUP BY id_item
            ) tx ON i.id = tx.id_item
            WHERE i.tipe = 'returnable'
              AND (COALESCE(d.total_dist, 0) + COALESCE(tx.net, 0)) > 0
            ORDER BY total_di_luar DESC
        """)
        return cur.fetchall()

def get_rincian_per_lantai(conn, id_item):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                l.nama AS nama_lantai,
                COALESCE(d.jumlah, 0) + COALESCE(tx.net, 0) AS jumlah_di_lantai
            FROM lantai l
            LEFT JOIN distribusi d ON d.id_lantai = l.id AND d.id_item = %s
            LEFT JOIN (
                SELECT id_lantai, SUM(jumlah) AS net
                FROM transaksi WHERE id_item = %s
                GROUP BY id_lantai
            ) tx ON tx.id_lantai = l.id
            WHERE COALESCE(d.jumlah, 0) + COALESCE(tx.net, 0) > 0
            ORDER BY l.id
        """, (id_item, id_item))
        return cur.fetchall()
