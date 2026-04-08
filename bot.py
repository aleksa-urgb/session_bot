import logging
import os
from datetime import datetime, date, timedelta
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)

import database as db
import excel_manager as xm
import export_helper as exp
from config import BOT_TOKEN, ADMIN_IDS, TIMEZONE

# ─────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# CONVERSATION STATES
# ─────────────────────────────────────────
(
    S_NAMA,
    S_NOMINAL,
    S_JML_AKUN,
    S_KET,  # Tambah Setoran (tanpa S_KAT)
    P_NAMA,
    P_NOMINAL,
    P_KET,
    P_KAT,  # Tambah Pengeluaran
    E_TYPE,
    E_ID,
    E_FIELD,
    E_VALUE,  # Edit
    K_ID,
    K_JML,  # Kurangi
    H_TYPE,
    H_ID,  # Hapus
    CARI_KW,  # Cari
    FILTER_PILIH,
    FILTER_TGL,  # Filter Rekap
    EXP_FORMAT,  # Export format
) = range(20)

BULAN_ID = [
    "",
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]


# ─────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────


def is_admin(user_id):
    return user_id in ADMIN_IDS


def idr(val):
    try:
        return f"Rp {int(val):,}".replace(",", ".")
    except:
        return "Rp 0"


def now_tgl():
    return datetime.now().strftime("%Y-%m-%d")


def now_jam():
    return datetime.now().strftime("%H:%M:%S")


def refresh_excel():
    try:
        all_s = db.get_all_setoran()
        all_p = db.get_all_pengeluaran()
        xm.rebuild_excel(all_s, all_p)
    except Exception as e:
        logger.error(f"Excel refresh error: {e}")


def log(update, aksi, detail=""):
    """Handle both Update and CallbackQuery objects"""
    if hasattr(update, "effective_user"):
        u = update.effective_user
    elif hasattr(update, "from_user"):
        u = update.from_user
    else:
        return
    db.log_aktivitas(u.id, u.username or u.first_name, aksi, detail)


def main_kb(user_id):
    btns = [
        [
            InlineKeyboardButton("💰 Tambah Setoran", callback_data="tambah_setoran"),
            InlineKeyboardButton(
                "💸 Tambah Keluar", callback_data="tambah_pengeluaran"
            ),
        ],
        [
            InlineKeyboardButton("📊 Statistik", callback_data="statistik"),
            InlineKeyboardButton("🔍 Cari Data", callback_data="cari"),
        ],
        [
            InlineKeyboardButton("📅 Rekap Harian", callback_data="rekap_hari"),
            InlineKeyboardButton("📆 Rekap Mingguan", callback_data="rekap_minggu"),
        ],
        [
            InlineKeyboardButton("🗓️ Rekap Bulanan", callback_data="rekap_bulan"),
            InlineKeyboardButton("📈 Rekap Tahunan", callback_data="rekap_tahun"),
        ],
        [
            InlineKeyboardButton("📤 Download Rekap", callback_data="download_menu"),
        ],
    ]
    if is_admin(user_id):
        btns += [
            [
                InlineKeyboardButton("✏️ Edit Data", callback_data="edit"),
                InlineKeyboardButton("➖ Kurangi Nominal", callback_data="kurangi"),
            ],
            [
                InlineKeyboardButton("🗑️ Hapus Data", callback_data="hapus"),
                InlineKeyboardButton("📤 Export Excel", callback_data="export_excel"),
            ],
            [
                InlineKeyboardButton("👤 Admin Panel", callback_data="admin_panel"),
            ],
        ]
    return InlineKeyboardMarkup(btns)


def back_kb():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_utama")]]
    )


# ─────────────────────────────────────────
# /start & /help
# ─────────────────────────────────────────


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if is_admin(u.id):
        teks = (
            f"👑 *Halo Boss {u.first_name}!*\n\n"
            "Mode *Admin AKTIF* — semua fitur tersedia.\n"
            "Pilih menu di bawah:"
        )
    else:
        teks = (
            f"👋 *Halo {u.first_name}!*\n\n"
            "Selamat datang di *Bot Rekap Setoran Tele* 💰\n"
            "Pilih menu di bawah:"
        )
    await update.message.reply_text(
        teks, parse_mode="Markdown", reply_markup=main_kb(u.id)
    )


async def menu_utama_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    u = query.from_user
    await query.edit_message_text(
        "🏠 *Menu Utama* — Pilih fitur:",
        parse_mode="Markdown",
        reply_markup=main_kb(u.id),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = (
        "📖 *PANDUAN BOT REKAP SETORAN TELE*\n\n"
        "💰 *Tambah Setoran* — Catat uang masuk setoran tele\n"
        "💸 *Tambah Keluar* — Catat pengeluaran/biaya\n"
        "📊 *Statistik* — Ringkasan total semua data\n"
        "🔍 *Cari Data* — Cari berdasarkan nama/keterangan\n"
        "📅 *Rekap Harian* — Rekap hari ini\n"
        "📆 *Rekap Mingguan* — Rekap minggu ini\n"
        "🗓️ *Rekap Bulanan* — Rekap bulan ini\n"
        "📈 *Rekap Tahunan* — Rekap tahun ini\n"
        "📤 *Download Rekap* — Download PDF atau TXT\n\n"
        "Admin tambahan:\n"
        "✏️ *Edit Data* — Ubah data yang sudah masuk\n"
        "➖ *Kurangi Nominal* — Kurangi jumlah setoran\n"
        "🗑️ *Hapus Data* — Hapus data transaksi\n"
        "📤 *Export Excel* — Kirim file Excel terbaru\n\n"
        "Gunakan /start untuk kembali ke menu."
    )
    await update.message.reply_text(teks, parse_mode="Markdown")


# ─────────────────────────────────────────
# TAMBAH SETORAN — kategori otomatis "Tele/Pulsa"
# ─────────────────────────────────────────


async def tambah_setoran_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "💰 *TAMBAH SETORAN TELE*\n\n"
        "Masukkan *nama penyetor*:\n_(kirim /batal untuk cancel)_",
        parse_mode="Markdown",
    )
    return S_NAMA


async def s_nama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_nama"] = update.message.text.strip()
    await update.message.reply_text(
        "💵 Masukkan *nominal* setoran (angka saja):", parse_mode="Markdown"
    )
    return S_NOMINAL


async def s_nominal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = int(update.message.text.replace(".", "").replace(",", ""))
        if val <= 0:
            raise ValueError
        context.user_data["s_nominal"] = val
        await update.message.reply_text(
            "👤 Masukkan *jumlah akun* yang disetor (angka saja):\n"
            "_(ketik `0` atau `-` jika tidak ada)_",
            parse_mode="Markdown",
        )
        return S_JML_AKUN
    except:
        await update.message.reply_text("❌ Nominal harus angka positif! Coba lagi:")
        return S_NOMINAL


async def s_jml_akun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = update.message.text.strip()
    try:
        jml = 0 if teks == "-" else int(teks.replace(".", "").replace(",", ""))
        if jml < 0:
            raise ValueError
        context.user_data["s_jml_akun"] = jml
        await update.message.reply_text(
            "📝 Masukkan *keterangan* (atau ketik `-` untuk skip):",
            parse_mode="Markdown",
        )
        return S_KET
    except:
        await update.message.reply_text(
            "❌ Jumlah akun harus angka (0 atau lebih)! Coba lagi:"
        )
        return S_JML_AKUN


async def s_ket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ket = update.message.text.strip() or "-"
    u = update.effective_user
    nama = context.user_data["s_nama"]
    nominal = context.user_data["s_nominal"]
    jml_akun = context.user_data.get("s_jml_akun", 0)
    kat = "Tele/Pulsa"  # otomatis

    new_id = db.tambah_setoran(
        nama=nama,
        nominal=nominal,
        keterangan=ket,
        kategori=kat,
        tanggal=now_tgl(),
        waktu=now_jam(),
        user_id=u.id,
        username=u.username or u.first_name,
        jml_akun=jml_akun,
    )
    refresh_excel()
    log(
        update,
        "TAMBAH_SETORAN",
        f"ID={new_id} nama={nama} nominal={nominal} jml_akun={jml_akun}",
    )

    akun_info = f"{jml_akun} akun" if jml_akun > 0 else "-"

    await update.message.reply_text(
        f"✅ *SETORAN BERHASIL DICATAT!*\n\n"
        f"📋 ID        : `{new_id}`\n"
        f"👤 Nama      : {nama}\n"
        f"💰 Nominal   : {idr(nominal)}\n"
        f"👤 Jml Akun  : {akun_info}\n"
        f"📝 Ket       : {ket}\n"
        f"🏷️ Kategori  : {kat}\n"
        f"📅 Tanggal   : {now_tgl()}  🕐 {now_jam()}\n\n"
        "_Excel telah diperbarui otomatis_ ✅",
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─────────────────────────────────────────
# TAMBAH PENGELUARAN
# ─────────────────────────────────────────


async def tambah_pengeluaran_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "💸 *TAMBAH PENGELUARAN*\n\n"
        "Masukkan *nama / keperluan*:\n_(kirim /batal untuk cancel)_",
        parse_mode="Markdown",
    )
    return P_NAMA


async def p_nama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["p_nama"] = update.message.text.strip()
    await update.message.reply_text(
        "💵 Masukkan *nominal* pengeluaran (angka saja):", parse_mode="Markdown"
    )
    return P_NOMINAL


async def p_nominal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = int(update.message.text.replace(".", "").replace(",", ""))
        if val <= 0:
            raise ValueError
        context.user_data["p_nominal"] = val
        await update.message.reply_text(
            "📝 Masukkan *keterangan* (atau ketik `-` untuk skip):",
            parse_mode="Markdown",
        )
        return P_KET
    except:
        await update.message.reply_text("❌ Nominal harus angka positif! Coba lagi:")
        return P_NOMINAL


async def p_ket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["p_ket"] = update.message.text.strip() or "-"
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🛒 Operasional", callback_data="pkat_ops"),
                InlineKeyboardButton("💼 Modal", callback_data="pkat_modal"),
            ],
            [
                InlineKeyboardButton("🏷️ Gaji", callback_data="pkat_gaji"),
                InlineKeyboardButton("📦 Lainnya", callback_data="pkat_lain"),
            ],
        ]
    )
    await update.message.reply_text(
        "🏷️ Pilih *kategori* pengeluaran:", parse_mode="Markdown", reply_markup=kb
    )
    return P_KAT


async def p_kat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kat_map = {
        "pkat_ops": "Operasional",
        "pkat_modal": "Modal",
        "pkat_gaji": "Gaji",
        "pkat_lain": "Lainnya",
    }
    kat = kat_map.get(q.data, "Lainnya")
    u = q.from_user
    nama = context.user_data["p_nama"]
    nominal = context.user_data["p_nominal"]
    ket = context.user_data["p_ket"]

    new_id = db.tambah_pengeluaran(
        nama=nama,
        nominal=nominal,
        keterangan=ket,
        kategori=kat,
        tanggal=now_tgl(),
        waktu=now_jam(),
        user_id=u.id,
        username=u.username or u.first_name,
    )
    refresh_excel()
    log(q, "TAMBAH_PENGELUARAN", f"ID={new_id} nama={nama} nominal={nominal}")

    await q.edit_message_text(
        f"✅ *PENGELUARAN BERHASIL DICATAT!*\n\n"
        f"📋 ID       : `{new_id}`\n"
        f"👤 Nama     : {nama}\n"
        f"💸 Nominal  : {idr(nominal)}\n"
        f"📝 Ket      : {ket}\n"
        f"🏷️ Kategori : {kat}\n"
        f"📅 Tanggal  : {now_tgl()}  🕐 {now_jam()}\n\n"
        "_Excel telah diperbarui otomatis_ ✅",
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─────────────────────────────────────────
# STATISTIK
# ─────────────────────────────────────────


async def statistik_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    all_s = db.get_all_setoran()
    all_p = db.get_all_pengeluaran()

    if not all_s and not all_p:
        await q.edit_message_text("📭 Belum ada data!", reply_markup=back_kb())
        return

    hari_ini = now_tgl()
    s_hari = [d for d in all_s if str(d["tanggal"]) == hari_ini]
    p_hari = [d for d in all_p if str(d["tanggal"]) == hari_ini]
    total_masuk = sum(d["nominal"] for d in all_s)
    total_keluar = sum(d["nominal"] for d in all_p)
    ur_total = total_masuk - total_keluar
    total_akun = sum(d.get("jml_akun", 0) or 0 for d in all_s)
    masuk_hari = sum(d["nominal"] for d in s_hari)
    keluar_hari = sum(d["nominal"] for d in p_hari)
    ur_hari = masuk_hari - keluar_hari
    akun_hari = sum(d.get("jml_akun", 0) or 0 for d in s_hari)

    teks = (
        "📊 *STATISTIK KESELURUHAN*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 *Total Semua:*\n"
        f"  Uang Masuk   : {idr(total_masuk)}\n"
        f"  Pengeluaran  : {idr(total_keluar)}\n"
        f"  Untung/Rugi  : {idr(ur_total)} {'✅' if ur_total >= 0 else '❌'}\n"
        f"  Jumlah Akun  : {total_akun} akun\n\n"
        f"📅 *Hari Ini ({hari_ini}):*\n"
        f"  Uang Masuk   : {idr(masuk_hari)}\n"
        f"  Pengeluaran  : {idr(keluar_hari)}\n"
        f"  Untung/Rugi  : {idr(ur_hari)} {'✅' if ur_hari >= 0 else '❌'}\n"
        f"  Jumlah Akun  : {akun_hari} akun\n\n"
        f"📦 *Jumlah Transaksi:*\n"
        f"  Total Masuk  : {len(all_s)} transaksi\n"
        f"  Total Keluar : {len(all_p)} transaksi\n"
    )
    if all_s:
        top = max(all_s, key=lambda x: x["nominal"])
        teks += f"\n🏆 *Setoran Terbesar:*\n  {top['nama']} — {idr(top['nominal'])}"

    await q.edit_message_text(teks, parse_mode="Markdown", reply_markup=back_kb())


# ─────────────────────────────────────────
# REKAP HELPERS
# ─────────────────────────────────────────


def _fmt_rekap(judul, s_data, p_data, rng):
    masuk = sum(d["nominal"] for d in s_data)
    keluar = sum(d["nominal"] for d in p_data)
    ur = masuk - keluar
    total_akun = sum(d.get("jml_akun", 0) or 0 for d in s_data)

    teks = (
        f"*{judul}*\n"
        f"📅 Periode : {rng}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Masuk   : {idr(masuk)} ({len(s_data)} transaksi)\n"
        f"💸 Keluar  : {idr(keluar)} ({len(p_data)} transaksi)\n"
        f"👤 Akun    : {total_akun} akun\n"
        f"{'✅' if ur >= 0 else '❌'} *{'Untung' if ur >= 0 else 'Rugi'}*  : {idr(abs(ur))}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    if s_data:
        teks += "💰 *Detail Setoran:*\n"
        for d in s_data[:10]:
            akun_info = (
                f" [{d.get('jml_akun', 0) or 0} akun]"
                if (d.get("jml_akun", 0) or 0) > 0
                else ""
            )
            teks += f"  • {d['nama']} — {idr(d['nominal'])}{akun_info}"
            if d.get("keterangan") and d["keterangan"] != "-":
                teks += f" _{d['keterangan']}_"
            teks += "\n"
        if len(s_data) > 10:
            teks += f"  _...dan {len(s_data)-10} lainnya_\n"
    if p_data:
        teks += "\n💸 *Detail Pengeluaran:*\n"
        for d in p_data[:10]:
            teks += f"  • {d['nama']} — {idr(d['nominal'])}"
            if d.get("keterangan") and d["keterangan"] != "-":
                teks += f" _{d['keterangan']}_"
            teks += "\n"
        if len(p_data) > 10:
            teks += f"  _...dan {len(p_data)-10} lainnya_\n"
    return teks


async def rekap_hari_cb(update, context):
    q = update.callback_query
    await q.answer()
    hari = now_tgl()
    s = db.get_setoran_range(hari, hari)
    p = db.get_pengeluaran_range(hari, hari)
    await q.edit_message_text(
        _fmt_rekap("📅 REKAP HARI INI", s, p, hari),
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )


async def rekap_minggu_cb(update, context):
    q = update.callback_query
    await q.answer()
    today = date.today()
    senin = today - timedelta(days=today.weekday())
    s = db.get_setoran_range(str(senin), str(today))
    p = db.get_pengeluaran_range(str(senin), str(today))
    rng = f"{senin.strftime('%d/%m/%Y')} s/d {today.strftime('%d/%m/%Y')}"
    await q.edit_message_text(
        _fmt_rekap("📆 REKAP MINGGU INI", s, p, rng),
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )


async def rekap_bulan_cb(update, context):
    q = update.callback_query
    await q.answer()
    today = date.today()
    awal = today.replace(day=1)
    s = db.get_setoran_range(str(awal), str(today))
    p = db.get_pengeluaran_range(str(awal), str(today))
    rng = f"{BULAN_ID[today.month]} {today.year}"
    await q.edit_message_text(
        _fmt_rekap("🗓️ REKAP BULAN INI", s, p, rng),
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )


async def rekap_tahun_cb(update, context):
    q = update.callback_query
    await q.answer()
    today = date.today()
    awal = date(today.year, 1, 1)
    s = db.get_setoran_range(str(awal), str(today))
    p = db.get_pengeluaran_range(str(awal), str(today))
    await q.edit_message_text(
        _fmt_rekap(f"📈 REKAP TAHUN {today.year}", s, p, str(today.year)),
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )


# ─────────────────────────────────────────
# CARI DATA
# ─────────────────────────────────────────


async def cari_start(update, context):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🔍 *CARI DATA*\n\nKetik kata kunci (nama / keterangan):", parse_mode="Markdown"
    )
    return CARI_KW


async def cari_proses(update, context):
    kw = update.message.text.strip()
    hasil_s = db.cari_setoran(kw)
    hasil_p = [
        d
        for d in db.get_all_pengeluaran()
        if kw.lower() in d["nama"].lower()
        or kw.lower() in (d.get("keterangan") or "").lower()
    ]

    if not hasil_s and not hasil_p:
        await update.message.reply_text(
            f"❌ Tidak ada hasil untuk *{kw}*",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        return ConversationHandler.END

    teks = f"🔍 *Hasil pencarian: '{kw}'*\n"
    if hasil_s:
        teks += f"\n💰 *Setoran ({len(hasil_s)}):*\n"
        for d in hasil_s[:8]:
            akun_info = (
                f" | {d.get('jml_akun', 0) or 0} akun"
                if (d.get("jml_akun", 0) or 0) > 0
                else ""
            )
            teks += f"  ID{d['id']} | {d['nama']} | {idr(d['nominal'])}{akun_info} | {d['tanggal']}\n"
    if hasil_p:
        teks += f"\n💸 *Pengeluaran ({len(hasil_p)}):*\n"
        for d in hasil_p[:8]:
            teks += (
                f"  ID{d['id']} | {d['nama']} | {idr(d['nominal'])} | {d['tanggal']}\n"
            )

    await update.message.reply_text(teks, parse_mode="Markdown", reply_markup=back_kb())
    return ConversationHandler.END


# ─────────────────────────────────────────
# EDIT DATA (Admin)
# ─────────────────────────────────────────


async def edit_start(update, context):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id):
        await q.answer("⛔ Akses ditolak!", show_alert=True)
        return ConversationHandler.END
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💰 Edit Setoran", callback_data="edit_setoran")],
            [
                InlineKeyboardButton(
                    "💸 Edit Pengeluaran", callback_data="edit_pengeluaran"
                )
            ],
        ]
    )
    await q.edit_message_text(
        "✏️ *EDIT DATA*\n\nPilih jenis data:", parse_mode="Markdown", reply_markup=kb
    )
    return E_TYPE


async def edit_type(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["edit_type"] = q.data
    await q.edit_message_text(
        "✏️ Masukkan *ID* data yang ingin diedit:", parse_mode="Markdown"
    )
    return E_ID


async def edit_id(update, context):
    try:
        eid = int(update.message.text.strip())
        etype = context.user_data["edit_type"]
        d = (
            db.get_setoran_by_id(eid)
            if etype == "edit_setoran"
            else db.get_pengeluaran_by_id(eid)
        )
        if not d:
            await update.message.reply_text("❌ Data tidak ditemukan!")
            return E_ID
        context.user_data["edit_id"] = eid
        akun_line = (
            f"Jml Akun   : {d.get('jml_akun', 0) or 0}\n"
            if etype == "edit_setoran"
            else ""
        )
        info = (
            f"📋 *Data ditemukan:*\n"
            f"Nama       : {d['nama']}\n"
            f"Nominal    : {idr(d['nominal'])}\n"
            f"{akun_line}"
            f"Keterangan : {d.get('keterangan', '-')}\n\n"
            "✏️ Field yang ingin diubah?\n"
            "Ketik: `nama`, `nominal`, `jml_akun`, `keterangan`, atau `kategori`"
        )
        await update.message.reply_text(info, parse_mode="Markdown")
        return E_FIELD
    except:
        await update.message.reply_text("❌ ID harus angka!")
        return E_ID


async def edit_field(update, context):
    field = update.message.text.strip().lower()
    if field not in ["nama", "nominal", "jml_akun", "keterangan", "kategori"]:
        await update.message.reply_text(
            "❌ Field tidak valid!\nPilih: `nama` / `nominal` / `jml_akun` / `keterangan` / `kategori`",
            parse_mode="Markdown",
        )
        return E_FIELD
    context.user_data["edit_field"] = field
    await update.message.reply_text(
        f"✏️ Masukkan *nilai baru* untuk `{field}`:", parse_mode="Markdown"
    )
    return E_VALUE


async def edit_value(update, context):
    val = update.message.text.strip()
    field = context.user_data["edit_field"]
    eid = context.user_data["edit_id"]
    etype = context.user_data["edit_type"]

    if field in ("nominal", "jml_akun"):
        try:
            val = int(val.replace(".", "").replace(",", ""))
        except:
            await update.message.reply_text("❌ Nilai harus angka!")
            return E_VALUE

    ok = (
        db.edit_setoran(eid, field, val)
        if etype == "edit_setoran"
        else db.edit_pengeluaran(eid, field, val)
    )

    if ok:
        refresh_excel()
        log(update, "EDIT_DATA", f"type={etype} id={eid} field={field} val={val}")
        await update.message.reply_text(
            f"✅ Data ID {eid} berhasil diupdate!\n"
            f"`{field}` → `{val}`\n\n_Excel telah diperbarui_ ✅",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
    else:
        await update.message.reply_text("❌ Gagal update data!")
    context.user_data.clear()
    return ConversationHandler.END


# ─────────────────────────────────────────
# KURANGI NOMINAL (Admin)
# ─────────────────────────────────────────


async def kurangi_start(update, context):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id):
        await q.answer("⛔ Akses ditolak!", show_alert=True)
        return ConversationHandler.END
    await q.edit_message_text(
        "➖ *KURANGI NOMINAL SETORAN*\n\nMasukkan *ID* setoran:", parse_mode="Markdown"
    )
    return K_ID


async def kurangi_id(update, context):
    try:
        kid = int(update.message.text.strip())
        d = db.get_setoran_by_id(kid)
        if not d:
            await update.message.reply_text("❌ Data tidak ditemukan!")
            return K_ID
        context.user_data["kurangi_id"] = kid
        context.user_data["kurangi_nominal_awal"] = d["nominal"]
        await update.message.reply_text(
            f"📋 ID {kid}: *{d['nama']}* — {idr(d['nominal'])}\n\n"
            "➖ Masukkan *jumlah yang dikurangi*:",
            parse_mode="Markdown",
        )
        return K_JML
    except:
        await update.message.reply_text("❌ ID harus angka!")
        return K_ID


async def kurangi_jml(update, context):
    try:
        jml = int(update.message.text.replace(".", "").replace(",", ""))
        kid = context.user_data["kurangi_id"]
        awal = context.user_data["kurangi_nominal_awal"]
        if jml >= awal:
            await update.message.reply_text(
                f"❌ Jumlah ({idr(jml)}) melebihi nominal saat ini ({idr(awal)})!\n"
                "Gunakan hapus data jika ingin menghapus seluruh setoran."
            )
            return K_JML
        db.kurangi_nominal_setoran(kid, jml)
        refresh_excel()
        log(update, "KURANGI_SETORAN", f"id={kid} kurang={jml}")
        await update.message.reply_text(
            f"✅ Berhasil dikurangi!\n"
            f"ID {kid}: {idr(awal)} → {idr(awal - jml)}\n\n_Excel telah diperbarui_ ✅",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )
        context.user_data.clear()
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ Jumlah harus angka!")
        return K_JML


# ─────────────────────────────────────────
# HAPUS DATA (Admin)
# ─────────────────────────────────────────


async def hapus_start(update, context):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id):
        await q.answer("⛔ Akses ditolak!", show_alert=True)
        return ConversationHandler.END
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💰 Hapus Setoran", callback_data="hps_setoran")],
            [
                InlineKeyboardButton(
                    "💸 Hapus Pengeluaran", callback_data="hps_pengeluaran"
                )
            ],
        ]
    )
    await q.edit_message_text(
        "🗑️ *HAPUS DATA*\n\nPilih jenis:", parse_mode="Markdown", reply_markup=kb
    )
    return H_TYPE


async def hapus_type(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["hapus_type"] = q.data
    await q.edit_message_text(
        "🗑️ Masukkan *ID* data yang ingin dihapus:", parse_mode="Markdown"
    )
    return H_ID


async def hapus_id(update, context):
    try:
        hid = int(update.message.text.strip())
        htype = context.user_data["hapus_type"]
        if htype == "hps_setoran":
            d = db.get_setoran_by_id(hid)
            ok = db.hapus_setoran(hid) if d else False
        else:
            d = db.get_pengeluaran_by_id(hid)
            ok = db.hapus_pengeluaran(hid) if d else False
        if ok:
            refresh_excel()
            log(update, "HAPUS_DATA", f"type={htype} id={hid}")
            await update.message.reply_text(
                f"✅ Data ID {hid} berhasil dihapus!\n_Excel telah diperbarui_ ✅",
                parse_mode="Markdown",
                reply_markup=back_kb(),
            )
        else:
            await update.message.reply_text(
                "❌ Data tidak ditemukan atau gagal dihapus!"
            )
        context.user_data.clear()
        return ConversationHandler.END
    except:
        await update.message.reply_text("❌ ID harus angka!")
        return H_ID


# ─────────────────────────────────────────
# DOWNLOAD REKAP (PDF / TXT)
# ─────────────────────────────────────────


async def download_menu_cb(update, context):
    q = update.callback_query
    await q.answer()
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📄 PDF Hari Ini", callback_data="dl_pdf_hari"),
                InlineKeyboardButton("📄 TXT Hari Ini", callback_data="dl_txt_hari"),
            ],
            [
                InlineKeyboardButton(
                    "📄 PDF Minggu Ini", callback_data="dl_pdf_minggu"
                ),
                InlineKeyboardButton(
                    "📄 TXT Minggu Ini", callback_data="dl_txt_minggu"
                ),
            ],
            [
                InlineKeyboardButton("📄 PDF Bulan Ini", callback_data="dl_pdf_bulan"),
                InlineKeyboardButton("📄 TXT Bulan Ini", callback_data="dl_txt_bulan"),
            ],
            [
                InlineKeyboardButton("📄 PDF Tahun Ini", callback_data="dl_pdf_tahun"),
                InlineKeyboardButton("📄 TXT Tahun Ini", callback_data="dl_txt_tahun"),
            ],
            [InlineKeyboardButton("🏠 Kembali", callback_data="menu_utama")],
        ]
    )
    await q.edit_message_text(
        "📤 *DOWNLOAD REKAP*\n\nPilih format dan periode:",
        parse_mode="Markdown",
        reply_markup=kb,
    )


async def _send_export(update, context, fmt, periode):
    q = update.callback_query
    await q.answer("⏳ Sedang membuat file...")
    today = date.today()

    if periode == "hari":
        tgl_awal = tgl_akhir = str(today)
        label = f"Harian_{today}"
        judul = f"📅 Rekap Harian — {today.strftime('%d/%m/%Y')}"
    elif periode == "minggu":
        senin = today - timedelta(days=today.weekday())
        tgl_awal, tgl_akhir = str(senin), str(today)
        label = f"Mingguan_{senin}_{today}"
        judul = f"📆 Rekap Mingguan — {senin.strftime('%d/%m')} s/d {today.strftime('%d/%m/%Y')}"
    elif periode == "bulan":
        tgl_awal = str(today.replace(day=1))
        tgl_akhir = str(today)
        label = f"Bulanan_{today.year}_{today.month:02}"
        judul = f"🗓️ Rekap Bulanan — {BULAN_ID[today.month]} {today.year}"
    else:
        tgl_awal = str(date(today.year, 1, 1))
        tgl_akhir = str(today)
        label = f"Tahunan_{today.year}"
        judul = f"📈 Rekap Tahunan — {today.year}"

    s = db.get_setoran_range(tgl_awal, tgl_akhir)
    p = db.get_pengeluaran_range(tgl_awal, tgl_akhir)
    r = db.summary_range(tgl_awal, tgl_akhir)

    try:
        path = (
            exp.export_pdf(judul, s, p, r, label)
            if fmt == "pdf"
            else exp.export_txt(judul, s, p, r, label)
        )
        caption = (
            f"📄 *Rekap PDF* — {judul}" if fmt == "pdf" else f"📝 *Rekap TXT* — {judul}"
        )
        with open(path, "rb") as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename=os.path.basename(path),
                caption=caption,
                parse_mode="Markdown",
            )
        os.remove(path)
    except Exception as e:
        logger.error(f"Export error: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"❌ Gagal membuat file: {e}"
        )


async def export_excel_cb(update, context):
    q = update.callback_query
    await q.answer("⏳ Menyiapkan Excel...")
    if not is_admin(q.from_user.id):
        await q.answer("⛔ Akses ditolak!", show_alert=True)
        return
    refresh_excel()
    from config import EXCEL_FILE

    if os.path.exists(EXCEL_FILE):
        with open(EXCEL_FILE, "rb") as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename=EXCEL_FILE,
                caption="📊 *File Excel Rekap Setoran*\n_Data real-time terbaru_",
                parse_mode="Markdown",
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ File Excel belum tersedia. Tambahkan data terlebih dahulu!",
        )


# ─────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────


async def admin_panel_cb(update, context):
    q = update.callback_query
    await q.answer()
    if not is_admin(q.from_user.id):
        await q.answer("⛔ Akses ditolak!", show_alert=True)
        return

    all_s = db.get_all_setoran()
    all_p = db.get_all_pengeluaran()
    total_masuk = sum(d["nominal"] for d in all_s)
    total_keluar = sum(d["nominal"] for d in all_p)
    total_akun = sum(d.get("jml_akun", 0) or 0 for d in all_s)

    teks = (
        "👤 *ADMIN PANEL*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Total Setoran     : {len(all_s)}\n"
        f"📦 Total Pengeluaran : {len(all_p)}\n"
        f"👤 Total Akun        : {total_akun} akun\n"
        f"💰 Total Masuk       : {idr(total_masuk)}\n"
        f"💸 Total Keluar      : {idr(total_keluar)}\n"
        f"{'✅ Untung' if total_masuk >= total_keluar else '❌ Rugi'}           : {idr(abs(total_masuk - total_keluar))}\n\n"
        "Database  : MySQL ✅\n"
        "Excel Sync: Otomatis ✅"
    )
    await q.edit_message_text(teks, parse_mode="Markdown", reply_markup=back_kb())


# ─────────────────────────────────────────
# CANCEL
# ─────────────────────────────────────────


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.message:
        await update.message.reply_text(
            "❌ Dibatalkan. Gunakan /start untuk kembali ke menu.",
            reply_markup=main_kb(update.effective_user.id),
        )
    return ConversationHandler.END


# ─────────────────────────────────────────
# CALLBACK ROUTER
# ─────────────────────────────────────────


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data

    routes = {
        "menu_utama": menu_utama_cb,
        "statistik": statistik_cb,
        "rekap_hari": rekap_hari_cb,
        "rekap_minggu": rekap_minggu_cb,
        "rekap_bulan": rekap_bulan_cb,
        "rekap_tahun": rekap_tahun_cb,
        "download_menu": download_menu_cb,
        "export_excel": export_excel_cb,
        "admin_panel": admin_panel_cb,
    }

    if data.startswith("dl_"):
        parts = data.split("_")
        await _send_export(update, context, parts[1], parts[2])
        return

    if data in routes:
        await routes[data](update, context)


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────


def main():
    db.init_database()
    refresh_excel()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation: Tambah Setoran (kategori otomatis, ada jml_akun)
    conv_setoran = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(tambah_setoran_start, pattern="^tambah_setoran$")
        ],
        states={
            S_NAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, s_nama)],
            S_NOMINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, s_nominal)],
            S_JML_AKUN: [MessageHandler(filters.TEXT & ~filters.COMMAND, s_jml_akun)],
            S_KET: [MessageHandler(filters.TEXT & ~filters.COMMAND, s_ket)],
        },
        fallbacks=[CommandHandler("batal", cancel), CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    # Conversation: Tambah Pengeluaran
    conv_pengeluaran = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                tambah_pengeluaran_start, pattern="^tambah_pengeluaran$"
            )
        ],
        states={
            P_NAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_nama)],
            P_NOMINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_nominal)],
            P_KET: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_ket)],
            P_KAT: [CallbackQueryHandler(p_kat, pattern="^pkat_")],
        },
        fallbacks=[CommandHandler("batal", cancel), CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    # Conversation: Cari
    conv_cari = ConversationHandler(
        entry_points=[CallbackQueryHandler(cari_start, pattern="^cari$")],
        states={
            CARI_KW: [MessageHandler(filters.TEXT & ~filters.COMMAND, cari_proses)],
        },
        fallbacks=[CommandHandler("batal", cancel)],
        allow_reentry=True,
    )

    # Conversation: Edit (Admin)
    conv_edit = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_start, pattern="^edit$")],
        states={
            E_TYPE: [
                CallbackQueryHandler(edit_type, pattern="^edit_(setoran|pengeluaran)$")
            ],
            E_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_id)],
            E_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field)],
            E_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value)],
        },
        fallbacks=[CommandHandler("batal", cancel)],
        allow_reentry=True,
    )

    # Conversation: Kurangi (Admin)
    conv_kurangi = ConversationHandler(
        entry_points=[CallbackQueryHandler(kurangi_start, pattern="^kurangi$")],
        states={
            K_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, kurangi_id)],
            K_JML: [MessageHandler(filters.TEXT & ~filters.COMMAND, kurangi_jml)],
        },
        fallbacks=[CommandHandler("batal", cancel)],
        allow_reentry=True,
    )

    # Conversation: Hapus (Admin)
    conv_hapus = ConversationHandler(
        entry_points=[CallbackQueryHandler(hapus_start, pattern="^hapus$")],
        states={
            H_TYPE: [CallbackQueryHandler(hapus_type, pattern="^hps_")],
            H_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, hapus_id)],
        },
        fallbacks=[CommandHandler("batal", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(conv_setoran)
    app.add_handler(conv_pengeluaran)
    app.add_handler(conv_cari)
    app.add_handler(conv_edit)
    app.add_handler(conv_kurangi)
    app.add_handler(conv_hapus)
    app.add_handler(CallbackQueryHandler(button_router))

    logger.info("🚀 Bot Rekap Setoran Tele aktif!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
