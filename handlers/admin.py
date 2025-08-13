from config import ADMIN_ID
import os

LOG_FILE_NAME = 'logs/bot.log'

async def send_logs(update, context) -> None:
    user_id = update.effective_user.id
    
    if user_id != int(ADMIN_ID):
        await update.message.reply_text(
            "⛔ <b>Ruxsat yo'q!</b>\n"
            "Bu buyruq faqat <b>admin</b> uchun mo'ljallangan.",
            parse_mode="HTML"
        )
        return

    if not os.path.exists(LOG_FILE_NAME):
        await update.message.reply_text(
            "📂 <b>Log fayli topilmadi</b>\n"
            "Hozircha log yozuvlari mavjud emas.",
            parse_mode="HTML"
        )
        return

    try:
        await update.message.reply_text(
            "📤 <b>Log fayli yuborilmoqda...</b>",
            parse_mode="HTML"
        )
        with open(LOG_FILE_NAME, "rb") as log_file:
            await update.message.reply_document(
                log_file,
                caption="✅ <b>Log fayli muvaffaqiyatli yuborildi</b>",
                parse_mode="HTML"
            )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ <b>Xatolik:</b> Faylni yuborishda muammo yuz berdi.\n"
            f"<code>{e}</code>",
            parse_mode="HTML"
        )
