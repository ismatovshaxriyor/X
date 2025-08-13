from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from database.models import User, Channels


async def _has_channel(user):
    """Foydalanuvchida kanal mavjudligini tekshiradi."""
    return Channels.get_or_none(user=user) is not None

async def _send_channel_warning(query):
    """Kanal yo'qligi haqida eslatma yuboradi."""
    await query.message.reply_text(
        "⚠️ <b>Kanal topilmadi!</b>\n\n"
        "📺 Siz hali kanal qo'shmagansiz!\n"
        "➕ /channels buyrug'i orqali kanal qo'shishingiz mumkin!",
        parse_mode="HTML"
    )

async def set_sentTo_callback(update, context):
    query = update.callback_query
    action = query.data.split('_', 1)[1]
    
    user_id = query.from_user.id
    await query.answer()

    user = User.get(telegram_id=user_id)

    send_to_map = {
        'user': 'user',
        'channel': 'channel',
        'userAndChannel': 'user_and_channel'
    }

    if action in send_to_map:
        if action != 'user' and not await _has_channel(user):
            await _send_channel_warning(query)
            return
        user.send_to = send_to_map[action]
        user.save()

    # Checkbox belgilari
    check_user = "✅" if user.send_to == 'user' else "⚪"
    check_channel = "✅" if user.send_to == 'channel' else "⚪"
    check_channel_and_user = "✅" if user.send_to == 'user_and_channel' else "⚪"
    
    btns = [
        [
            InlineKeyboardButton(text=f"{check_user} O'zimga", callback_data='sendTo_user'),
            InlineKeyboardButton(text=f"{check_channel} Kanallarga", callback_data='sendTo_channel')
        ],
        [
            InlineKeyboardButton(text=f"{check_channel_and_user} O'zimga va Kanallarga", callback_data='sendTo_userAndChannel')
        ]
    ]

    # Foydalanuvchi ma'lumotlari
    status_emoji = "🟢" if user.is_monitoring_active else "🔴"
    status_text = "Faol" if user.is_monitoring_active else "Faol emas"
    
    text = f"""👤 <b>Profil Ma'lumotlari</b>

🆔 <b>Foydalanuvchi:</b> {user.first_name}
⭐ <b>Stars balansi:</b> {user.stars}
{status_emoji} <b>Kuzatish holati:</b> {status_text}

📊 <b>Gift sozlamalari:</b>
   🔻 <b>Minimal:</b> {user.min_stars if user.min_stars != None else '❌ Belgilanmagan'}
   🔺 <b>Maksimal:</b> {user.max_stars if user.max_stars != None else '❌ Belgilanmagan'}
   🎯 <b>Gift limiti:</b> {user.gift_limit if user.gift_limit else "♾️ Chegaralanmagan"}

📅 <b>Qo'shilgan sana:</b> {str(user.joined_at).split(".")[0]}

📤 <b>Gift yuborish manzili:</b>"""

    try:
        await query.message.edit_text(
            text=text, 
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="HTML"
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            await query.message.reply_text(
                "⚠️ <b>Xato yuz berdi!</b>\n\n"
                "🔄 Iltimos, qayta urinib ko'ring.",
                parse_mode="HTML"
            )
