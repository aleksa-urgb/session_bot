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
import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "bot_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Aleksa_1512")
DB_NAME = os.environ.get("DB_NAME", "rekap_setoran")
BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8747446983:AAFE3GZ7mliq7fCPbbSLdZhLyA0rv2thWmk"
)
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "1314664080").split(",")]


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
