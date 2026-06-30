import telebot
from telebot import types
from datetime import datetime
import logging
import re

# TOKEN BOT TELEGRAM KAMU
TOKEN = 'TOKEN KAMU '

# Mematikan semua log bawaan telebot agar Termux tidak spam teks
logger = telebot.logger
telebot.logger.setLevel(logging.CRITICAL) 

bot = telebot.TeleBot(TOKEN)
db = {}

def get_waktu_indonesia():
    hari_indo = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
    now = datetime.now()
    
    indeks_hari = int(now.strftime("%w"))
    hari = hari_indo[indeks_hari]
    
    tanggal = now.strftime("%d")
    bulan = str(int(now.strftime("%m")))
    tahun = now.strftime("%Y")
    
    return f"{hari}, {tanggal}/{bulan}/{tahun}"

def proses_dan_pecah_laporan(teks):
    list_bersih = []
    # Pola regex untuk menangkap blok valid dari 'User:' sampai angka setelah 'Shift:'
    pattern = r'(?i)(User:\s*.*?Shift:\s*\d+)'
    matches = re.findall(pattern, teks, re.DOTALL)
    
    for blok in matches:
        sub_teks = blok.strip()
        if sub_teks.lower().startswith("user:"):
            sub_teks = "User:" + sub_teks[5:]
        if sub_teks:
            list_bersih.append(sub_teks)
            
    return list_bersih

def generate_laporan_teks(chat_id):
    session = db.get(chat_id)
    if not session:
        return "Belum ada laporan yang diinput."

    waktu_str = get_waktu_indonesia()
    txt = f"#Shift_report\n"
    txt += f"Shift#{session['shift']} {waktu_str}\n"
    txt += f"(O: {session['nama']})\n\n"

    for index, item in enumerate(session['laporan'], start=1):
        txt += f"{index}.\n{item}\n\n"

    return txt.strip()

# ==================== KEYBOARD MENU UTAMA ====================
def kirim_menu_utama(chat_id, pesan_teks="Gunakan menu di bawah untuk mengelola:"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_lihat = types.KeyboardButton('👀 Lihat Hasil Laporan')
    btn_edit = types.KeyboardButton('✏️ Edit Poin Laporan')
    btn_hapus = types.KeyboardButton('❌ Hapus Poin Laporan')
    btn_reset = types.KeyboardButton('🔄 Reset Semua Data')
    btn_kirim = types.KeyboardButton('🚀 Kirim/Selesai')
    
    markup.add(btn_lihat, btn_edit)
    markup.add(btn_hapus, btn_reset)
    markup.add(btn_kirim)
    
    bot.send_message(chat_id, pesan_teks, reply_markup=markup)

# ==================== COMMAND /START ====================
@bot.message_handler(commands=['start'])
def welcome(message):
    chat_id = message.chat.id
    db[chat_id] = {'shift': '', 'nama': '', 'laporan': [], 'status': '', 'target_index': -1}

    bot.send_message(chat_id, "SEMANGAT KERJA BRO 😁AWALI DENGAN BISMILLAH !! ,GK USAH SPANENG 🤣🤣")

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("Shift 1", callback_data="set_shift_1")
    btn2 = types.InlineKeyboardButton("Shift 2", callback_data="set_shift_2")
    btn3 = types.InlineKeyboardButton("Shift 3", callback_data="set_shift_3")
    markup.add(btn1, btn2, btn3)

    bot.send_message(chat_id, "Pilih Shift Kerja Kamu:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_shift_'))
def callback_shift(call):
    chat_id = call.message.chat.id
    shift_num = call.data.split('_')[2]

    if chat_id not in db:
        db[chat_id] = {'shift': '', 'nama': '', 'laporan': [], 'status': '', 'target_index': -1}

    db[chat_id]['shift'] = shift_num
    db[chat_id]['status'] = 'WAITING_NAME'
    
    bot.answer_callback_query(call.id)
    bot.send_message(chat_id, f"Kamu memilih Shift {shift_num}.\n\nSekarang masukkan nama Operator (Contoh: Ainul, Rifki & Akbar):")

# ==================== HANDLING INPUT TEKS & MENU ====================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    teks_input = message.text

    if chat_id not in db:
        bot.send_message(chat_id, "Silahkan ketik /start untuk memulai bot laporan.")
        return

    session = db[chat_id]

    if teks_input == '👀 Lihat Hasil Laporan':
        bot.send_message(chat_id, generate_laporan_teks(chat_id))
        return

    elif teks_input == '❌ Hapus Poin Laporan':
        if session['laporan']:
            session['status'] = 'WAITING_DELETE_NUMBER'
            bot.send_message(chat_id, f"Total ada {len(session['laporan'])} poin laporan.\n\nMasukkan NOMOR berapa yang mau kamu hapus:")
        else:
            bot.send_message(chat_id, "Tidak ada poin laporan untuk dihapus.")
        return

    elif teks_input == '✏️ Edit Poin Laporan':
        if session['laporan']:
            session['status'] = 'WAITING_EDIT_NUMBER'
            bot.send_message(chat_id, f"Total ada {len(session['laporan'])} poin laporan.\n\nMasukkan NOMOR berapa yang mau kamu edit:")
        else:
            bot.send_message(chat_id, "Belum ada poin yang bisa diedit.")
        return

    elif teks_input == '🔄 Reset Semua Data':
        session['laporan'] = []
        bot.send_message(chat_id, "Semua poin laporan berhasil di-reset!")
        bot.send_message(chat_id, generate_laporan_teks(chat_id))
        kirim_menu_utama(chat_id)
        return

    elif teks_input == '🚀 Kirim/Selesai':
        hasil_akhir = generate_laporan_teks(chat_id)
        bot.send_message(chat_id, hasil_akhir)
        bot.send_message(chat_id, "Laporan final selesai dibuat! Ketik /start jika ingin membuat laporan baru.")
        return

    # --- LOGIKA STATE MACHINE ---
    if session['status'] == 'WAITING_NAME':
        session['nama'] = teks_input
        session['status'] = ''
        caption_awal = generate_laporan_teks(chat_id)
        bot.send_message(chat_id, caption_awal)
        kirim_menu_utama(chat_id, "Caption awal dibuat! Kamu bisa langsung paste laporan gabungan di sini:")
        
    elif session['status'] == 'WAITING_DELETE_NUMBER':
        try:
            nomor = int(teks_input)
            if 1 <= nomor <= len(session['laporan']):
                session['laporan'].pop(nomor - 1)
                session['status'] = ''
                bot.send_message(chat_id, f"✅ Poin nomor {nomor} berhasil dihapus! Penomoran otomatis diperbarui.")
                bot.send_message(chat_id, generate_laporan_teks(chat_id))
                kirim_menu_utama(chat_id)
            else:
                bot.send_message(chat_id, f"❌ Nomor salah. Masukkan angka antara 1 sampai {len(session['laporan'])}:")
        except ValueError:
            bot.send_message(chat_id, "❌ Input harus berupa angka. Silahkan masukkan nomor kembali:")

    elif session['status'] == 'WAITING_EDIT_NUMBER':
        try:
            nomor = int(teks_input)
            if 1 <= nomor <= len(session['laporan']):
                session['target_index'] = nomor - 1
                session['status'] = 'WAITING_EDIT_TEXT'
                bot.send_message(chat_id, f"Isi Poin Nomor {nomor} saat ini adalah:\n\n{session['laporan'][nomor - 1]}\n\nSilahkan paste REVISI TERBARU (Wajib ada kata 'User:'):")
            else:
                bot.send_message(chat_id, f"❌ Nomor salah. Masukkan angka antara 1 sampai {len(session['laporan'])}:")
        except ValueError:
            bot.send_message(chat_id, "❌ Input harus berupa angka. Silahkan masukkan nomor kembali:")

    elif session['status'] == 'WAITING_EDIT_TEXT':
        # DI SINI FILTERS PENGETATAN EDIT:
        # Cek apakah teks input mengandung kata 'User:' secara fleksibel
        if not re.search(r'(?i)\bUser:', teks_input):
            session['status'] = ''
            session['target_index'] = -1
            bot.send_message(chat_id, "❌ GAGAL EDIT! Teks revisi tidak valid karena tidak mengandung kata 'User:'. Laporan tidak berubah.")
            kirim_menu_utama(chat_id)
            return
            
        blok_edit = proses_dan_pecah_laporan(teks_input)
        idx = session['target_index']
        
        if blok_edit:
            session['laporan'][idx] = blok_edit[0]
            bot.send_message(chat_id, "✅ Poin berhasil diperbarui!")
        else:
            # Proteksi tambahan jika user ketik 'User:' tapi format shift-nya rusak
            bot.send_message(chat_id, "❌ GAGAL EDIT! Format data di bawah kata 'User:' tidak lengkap.")
            
        session['status'] = ''
        session['target_index'] = -1
        bot.send_message(chat_id, generate_laporan_teks(chat_id))
        kirim_menu_utama(chat_id)
        
    else:
        # Proses paste borongan secara normal
        blok_laporan_baru = proses_dan_pecah_laporan(teks_input)
        
        if blok_laporan_baru:
            session['laporan'].extend(blok_laporan_baru)
            bot.send_message(chat_id, generate_laporan_teks(chat_id))
            kirim_menu_utama(chat_id)
        else:
            bot.send_message(chat_id, "❌ Format salah. Pastikan teks yang di-paste berisi data 'User:' sampai 'Shift:'.")

print("========================================")
print(" Bot Laporan Shift Aktif & Kondusif! ")
print("========================================")

bot.infinity_polling()
