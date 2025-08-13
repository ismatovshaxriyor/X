import functools
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import User


def require_agreement(func):
    @functools.wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        user = User.get(telegram_id=user_id)

        if not user:
            await update.message.reply_text("❌ Siz ro'yxatdan o'tmagansiz\n\nIltimos /start buyrug'ini qayta bosing!")

        if not user.is_agree:
            # Tugmalar
            keyboard = [
                [InlineKeyboardButton("✅ Roziman", callback_data=f"agree_{user_id}")],
                [InlineKeyboardButton("❌ Rad etaman", callback_data=f"disagree_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Chiroyli ko‘rinishdagi ogohlantirish
            warning_text = (
                "⚠️ <b>Ogohlantirish</b>\n\n"
                "Ushbu bot orqali <b>Telegram Gift</b>larini sotib olish imkoniyati "
                "<u>Telegram tomonidan rasmiy tarzda qo'llab-quvvatlanmaydi</u>.\n\n"
                "📌 <b>Diqqat!</b> Botdan foydalanish natijasida yuzaga kelishi mumkin bo'lgan:\n"
                "  • 💰 To'lov muammolari\n"
                "  • 🚫 Hisob bloklanishi\n"
                "  • ⭐ Qolib ketgan Stars yo'qotilishi\n"
                "uchun <b>biz javobgar emasmiz</b>.\n\n"
                "❗ Agar botimiz Telegram tomonidan bloklansa, qolib ketgan Stars'laringizni qaytarib bera olmaymiz."
            )

            await update.message.reply_text(
                warning_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


async def agreement_callback_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("agree_"):
        user_id = int(query.data.split("_")[1])
        user = User.get(telegram_id=user_id)
        user.is_agree = True
        user.save()

        success_text = (
            "✅ <b>Roziligingiz qabul qilindi!</b>\n\n"
            "Endi botning barcha funksiyalaridan foydalanishingiz mumkin. 🎉\n"
            "➡️ /premium buyrug'ini qayta yuboring."
        )
        await query.edit_message_text(success_text, parse_mode="HTML")

    elif query.data.startswith("disagree_"):
        fail_text = (
            "❌ <b>Rozilik rad etildi</b>\n\n"
            "Afsuski, shartlarga rozilik bermasangiz sizni premium foydalanuvchi qila olmaymiz."
        )
        await query.edit_message_text(fail_text, parse_mode="HTML")
