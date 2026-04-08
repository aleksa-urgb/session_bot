"""
database.py - MySQL Database Manager untuk Bot Rekap Setoran Tele
"""

import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime, date
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

logger = logging.getLogger(__name__)


def get_connection():
    """Buat koneksi ke MySQL"""
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        autocommit=True
    )


def init_database():
    """Buat tabel jika belum ada"""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabel setoran (uang masuk)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS setoran (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            nama        VARCHAR(100) NOT NULL,
            nominal     BIGINT NOT NULL DEFAULT 0,
            keterangan  TEXT,
            kategori    VARCHAR(50) DEFAULT 'setoran',
            tanggal     DATE NOT NULL,
            waktu       TIME NOT NULL,
            user_id     BIGINT,
            username    VARCHAR(100),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_deleted  TINYINT(1) DEFAULT 0
        )
    """)

    # Tabel pengeluaran (uang keluar)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pengeluaran (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            nama        VARCHAR(100) NOT NULL,
            nominal     BIGINT NOT NULL DEFAULT 0,
            keterangan  TEXT,
            kategori    VARCHAR(50) DEFAULT 'pengeluaran',
            tanggal     DATE NOT NULL,
            waktu       TIME NOT NULL,
            user_id     BIGINT,
            username    VARCHAR(100),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_deleted  TINYINT(1) DEFAULT 0
        )
    """)

    # Tabel log aktivitas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_aktivitas (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            user_id     BIGINT,
            username    VARCHAR(100),
            aksi        VARCHAR(100),
            detail      TEXT,
            waktu       DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    logger.info("✅ Database terinitialisasi!")


# =====================
# SETORAN (UANG MASUK)
# =====================

def tambah_setoran(nama, nominal, keterangan, kategori, tanggal, waktu, user_id, username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO setoran (nama, nominal, keterangan, kategori, tanggal, waktu, user_id, username)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (nama, nominal, keterangan, kategori, tanggal, waktu, user_id, username))
    new_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return new_id


def get_setoran_by_id(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM setoran WHERE id=%s AND is_deleted=0", (id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def edit_setoran(id, field, value):
    allowed = ['nama', 'nominal', 'keterangan', 'kategori', 'tanggal']
    if field not in allowed:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE setoran SET {field}=%s WHERE id=%s AND is_deleted=0", (value, id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0


def kurangi_nominal_setoran(id, jumlah):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE setoran SET nominal=nominal-%s WHERE id=%s AND is_deleted=0", (jumlah, id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0


def hapus_setoran(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE setoran SET is_deleted=1 WHERE id=%s", (id,))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0


def cari_setoran(keyword):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    like = f"%{keyword}%"
    cursor.execute("""
        SELECT * FROM setoran
        WHERE is_deleted=0 AND (nama LIKE %s OR keterangan LIKE %s OR kategori LIKE %s)
        ORDER BY tanggal DESC, waktu DESC LIMIT 20
    """, (like, like, like))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_setoran_range(tgl_mulai, tgl_akhir):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM setoran
        WHERE is_deleted=0 AND tanggal BETWEEN %s AND %s
        ORDER BY tanggal DESC, waktu DESC
    """, (tgl_mulai, tgl_akhir))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_all_setoran():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM setoran WHERE is_deleted=0 ORDER BY tanggal DESC, waktu DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# =======================
# PENGELUARAN (UANG KELUAR)
# =======================

def tambah_pengeluaran(nama, nominal, keterangan, kategori, tanggal, waktu, user_id, username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pengeluaran (nama, nominal, keterangan, kategori, tanggal, waktu, user_id, username)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (nama, nominal, keterangan, kategori, tanggal, waktu, user_id, username))
    new_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return new_id


def get_pengeluaran_by_id(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pengeluaran WHERE id=%s AND is_deleted=0", (id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def edit_pengeluaran(id, field, value):
    allowed = ['nama', 'nominal', 'keterangan', 'kategori', 'tanggal']
    if field not in allowed:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE pengeluaran SET {field}=%s WHERE id=%s AND is_deleted=0", (value, id))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0


def hapus_pengeluaran(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pengeluaran SET is_deleted=1 WHERE id=%s", (id,))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return affected > 0


def get_pengeluaran_range(tgl_mulai, tgl_akhir):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM pengeluaran
        WHERE is_deleted=0 AND tanggal BETWEEN %s AND %s
        ORDER BY tanggal DESC, waktu DESC
    """, (tgl_mulai, tgl_akhir))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_all_pengeluaran():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pengeluaran WHERE is_deleted=0 ORDER BY tanggal DESC, waktu DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# =====================
# RINGKASAN / SUMMARY
# =====================

def summary_range(tgl_mulai, tgl_akhir):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COALESCE(SUM(nominal),0) as total, COUNT(*) as jumlah
        FROM setoran WHERE is_deleted=0 AND tanggal BETWEEN %s AND %s
    """, (tgl_mulai, tgl_akhir))
    s = cursor.fetchone()

    cursor.execute("""
        SELECT COALESCE(SUM(nominal),0) as total, COUNT(*) as jumlah
        FROM pengeluaran WHERE is_deleted=0 AND tanggal BETWEEN %s AND %s
    """, (tgl_mulai, tgl_akhir))
    p = cursor.fetchone()

    cursor.close()
    conn.close()

    masuk = int(s['total'])
    keluar = int(p['total'])
    return {
        'masuk': masuk,
        'keluar': keluar,
        'untung_rugi': masuk - keluar,
        'jml_setoran': s['jumlah'],
        'jml_pengeluaran': p['jumlah']
    }


def log_aktivitas(user_id, username, aksi, detail):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO log_aktivitas (user_id, username, aksi, detail)
            VALUES (%s, %s, %s, %s)
        """, (user_id, username, aksi, detail))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Log error: {e}")
