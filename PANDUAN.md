# 🤖 Bot Rekap Setoran Tele — Panduan Lengkap

## 📁 Struktur File

```
rekap_bot/
├── bot.py              ← File utama bot
├── database.py         ← Manager MySQL
├── excel_manager.py    ← Excel real-time
├── export_helper.py    ← Generator PDF & TXT
├── config.py           ← Konfigurasi (EDIT INI DULU!)
├── requirements.txt    ← Library Python
├── Procfile            ← Untuk hosting Railway
└── PANDUAN.md          ← File ini
```

---

## ⚙️ LANGKAH 1 — Isi config.py

Buka `config.py` dan isi:

```python
BOT_TOKEN   = "TOKEN_BOT_KAMU"       # Dari @BotFather
ADMIN_IDS   = [123456789]            # Telegram User ID kamu
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = "password_mysql_kamu"
DB_NAME     = "rekap_setoran"
```

### Cara cek Telegram User ID kamu:
1. Buka Telegram
2. Cari bot **@userinfobot**
3. Klik Start → ID kamu akan tampil

### Cara buat Bot Token:
1. Cari **@BotFather** di Telegram
2. Ketik `/newbot`
3. Ikuti instruksi, copy TOKEN yang diberikan

---

## ⚙️ LANGKAH 2 — Setup MySQL

### Install MySQL (Ubuntu/Linux):
```bash
sudo apt update
sudo apt install mysql-server -y
sudo mysql_secure_installation
```

### Buat database:
```sql
CREATE DATABASE rekap_setoran CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'botuser'@'localhost' IDENTIFIED BY 'password_kuat';
GRANT ALL PRIVILEGES ON rekap_setoran.* TO 'botuser'@'localhost';
FLUSH PRIVILEGES;
```
> Tabel dibuat **otomatis** saat bot pertama kali jalan.

---

## ⚙️ LANGKAH 3 — Install & Jalankan Lokal

```bash
# Buat virtual environment
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# Install library
pip install -r requirements.txt

# Jalankan bot
python bot.py
```

---

## 🌐 HOSTING GRATIS — Railway.app (RECOMMENDED)

Railway adalah platform hosting gratis yang paling mudah untuk bot Telegram.

### Langkah demi langkah:

**1. Daftar akun**
- Buka https://railway.app
- Daftar pakai GitHub (gratis)

**2. Buat MySQL di Railway:**
- Klik `+ New Project`
- Pilih `Database → Add MySQL`
- Tunggu sampai selesai deploy
- Klik MySQL → tab `Connect`
- Catat: Host, Port, Username, Password, Database

**3. Upload kode ke GitHub:**
```bash
git init
git add .
git commit -m "Bot rekap setoran"
git remote add origin https://github.com/USERNAME/REPO_KAMU.git
git push -u origin main
```

**4. Deploy bot ke Railway:**
- Di Railway, klik `+ New Service`
- Pilih `GitHub Repo`
- Pilih repo yang baru kamu upload
- Masuk ke tab `Variables`, tambahkan:

| Variable       | Value                        |
|----------------|------------------------------|
| BOT_TOKEN      | token bot kamu               |
| DB_HOST        | host MySQL dari Railway      |
| DB_PORT        | port MySQL dari Railway      |
| DB_USER        | user MySQL dari Railway      |
| DB_PASSWORD    | password MySQL dari Railway  |
| DB_NAME        | nama database                |
| ADMIN_IDS      | 123456789                    |

**5. Update config.py untuk baca ENV:**

Ganti `config.py` bagian database menjadi:
```python
import os
DB_HOST     = os.environ.get("DB_HOST", "localhost")
DB_PORT     = int(os.environ.get("DB_PORT", 3306))
DB_USER     = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME     = os.environ.get("DB_NAME", "rekap_setoran")
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "TOKEN_LOKAL")
ADMIN_IDS   = [int(x) for x in os.environ.get("ADMIN_IDS", "123456789").split(",")]
```

**6. Deploy ulang** — Railway otomatis rebuild setiap kamu push ke GitHub.

Bot akan jalan **24/7 gratis** (batas 500 jam/bulan di plan Starter).

---

## 🌐 ALTERNATIF HOSTING GRATIS LAIN

### Render.com
- Daftar di https://render.com
- Buat `Web Service` (pilih Worker)
- Sama seperti Railway tapi pakai PostgreSQL (butuh ganti DB driver)

### Fly.io
- Install flyctl: `curl -L https://fly.io/install.sh | sh`
- `fly launch` di folder bot
- Gratis untuk app kecil

---

## 📱 CARA PAKAI BOT

### Menu User Biasa:
| Tombol | Fungsi |
|--------|--------|
| 💰 Tambah Setoran | Catat uang masuk dari penjual tele |
| 💸 Tambah Keluar | Catat pengeluaran/biaya |
| 📊 Statistik | Ringkasan total semua data |
| 🔍 Cari Data | Cari berdasarkan nama |
| 📅 Rekap Harian | Rekap hari ini |
| 📆 Rekap Mingguan | Rekap 7 hari (Senin-sekarang) |
| 🗓️ Rekap Bulanan | Rekap bulan ini |
| 📈 Rekap Tahunan | Rekap tahun ini |
| 📤 Download Rekap | Download PDF atau TXT |

### Menu Admin Tambahan:
| Tombol | Fungsi |
|--------|--------|
| ✏️ Edit Data | Ubah nama/nominal/keterangan |
| ➖ Kurangi Nominal | Kurangi jumlah setoran |
| 🗑️ Hapus Data | Hapus transaksi |
| 📤 Export Excel | Kirim file .xlsx terbaru |
| 👤 Admin Panel | Ringkasan + status sistem |

---

## 📊 Fitur Excel Real-Time

File `rekap_setoran.xlsx` otomatis diperbarui setiap ada:
- Tambah data baru ✅
- Edit data ✅
- Kurangi nominal ✅
- Hapus data ✅

### Sheet yang ada di Excel:
1. 💰 **Setoran Masuk** — semua transaksi masuk
2. 💸 **Pengeluaran** — semua transaksi keluar
3. 📊 **Ringkasan** — total masuk, keluar, untung/rugi
4. 📅 **Harian** — rekap per hari
5. 📆 **Mingguan** — rekap per minggu
6. 🗓️ **Bulanan** — rekap per bulan
7. 📈 **Tahunan** — rekap per tahun

---

## ❓ TROUBLESHOOTING

**Bot tidak bisa konek ke MySQL:**
```
Error: Can't connect to MySQL server
```
→ Pastikan MySQL jalan: `sudo systemctl start mysql`
→ Cek HOST, USER, PASSWORD di config.py

**Library tidak ditemukan:**
```
ModuleNotFoundError: No module named 'telegram'
```
→ Jalankan: `pip install -r requirements.txt`

**Bot tidak mau start di Railway:**
→ Pastikan ada file `Procfile` dengan isi: `worker: python bot.py`
→ Cek tab Logs di Railway untuk error detail

---

## 📞 Kontak & Support

Bot dibuat dengan Python + python-telegram-bot v21
Database: MySQL | Excel: openpyxl | PDF: ReportLab
