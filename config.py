"""
config.py - Konfigurasi Bot
Ganti semua nilai di sini sesuai kebutuhan
"""

# ============================
# 🤖 TOKEN BOT TELEGRAM
# ============================
BOT_TOKEN = "8747446983:AAFE3GZ7mliq7fCPbbSLdZhLyA0rv2thWmk"

# ============================
# 👑 ADMIN IDs
# Cara cek ID kamu: chat ke @userinfobot di Telegram
# ============================
ADMIN_IDS = [1314664080]  # Ganti dengan Telegram user ID kamu

# ============================
# 🗄️ KONFIGURASI MYSQL
# ============================
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "botuser"
DB_PASSWORD = "Aleksa_1512"
DB_NAME = "rekap_setoran"
DB_UNIX_SOCKET = (
    "/var/run/mysqld/mysqld.sock"  # Untuk Ubuntu/Linux (hapus jika Windows)
)

# ============================
# 📁 FILE OUTPUT
# ============================
EXCEL_FILE = "rekap_setoran.xlsx"
PDF_DIR = "pdf_exports"
TXT_DIR = "txt_exports"

# ============================
# ⚙️ PENGATURAN BOT
# ============================
TIMEZONE = "Asia/Jakarta"
MAX_EXPORT_ROWS = 1000
