from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")

async def shift_report(update: Update, context: ContextTypes.DEFAULT_TYPE):

    caption = update.message.caption

    if not caption:
        return

    if "#Shift_report" not in caption:
        return

    waktu = datetime.now().strftime("%d/%m/%Y %H:%M")

    hasil = f"""
{caption}

Laporan shift

----------------
Dikirim: {update.message.from_user.first_name}
Waktu: {waktu}
"""

    await update.message.reply_text(hasil)


app = Application.builder().token(TOKEN).build()

app.add_handler(
    MessageHandler(filters.CAPTION, shift_report)
)

app.run_polling()
