from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Channels, User

async def back_channels_callback(update, context):
    """Kanallar ro'yxatiga qaytish funksiyasi"""
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    # Foydalanuvchini olish
    user = User.get(telegram_id=user_id)

    # Foydalanuvchiga tegishli kanallarni olish
    try:
        channels = list(Channels.select().where(Channels.user == user))
    except Exception as e:
        channels = []

    btns = []

    if channels:
        # Kanallar ro'yxatini yaratish
        for i, channel in enumerate(channels):
            btn = InlineKeyboardButton(
                text=f"📺 {i+1}. {channel.channel_name}",
                callback_data=f"chnl_{channel.channel_id}"
            )

            if i % 2 == 0:
                btns.append([btn])
            else:
                btns[-1].append(btn)

        # Kanal qo'shish tugmasi
        btns.append([
            InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="add_channel")
        ])

        await query.message.edit_text(
            "📺 <b>Sizning kanallaringiz:</b>\n\n"
            "🎁 Giftlar shu kanallarga yuboriladi\n"
            "⚙️ Boshqarish uchun kanal nomini bosing\n"
            "➕ Yangi kanal qo'shish ham mumkin",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="HTML"
        )
    else:
        # Agar kanal bo'lmasa
        btns.append([
            InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")
        ])
        
        await query.message.edit_text(
            "📺 <b>Kanallar bo'limi</b>\n\n"
            "❌ Siz hali kanal qo'shmadingiz\n"
            "🚀 Birinchi kanalingizni qo'shing!",
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="HTML"
        )
