from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Channels

async def get_channel_callback(update, context):
    """Callback orqali kanal ma'lumotlarini chiqarish"""
    query = update.callback_query
    await query.answer()

    try:
        _, chnl_id = query.data.split('_', 1)

        channel = Channels.get(Channels.channel_id == chnl_id)

        text = f"""📺 <b>Kanal Ma'lumotlari</b>

🏷️ <b>Nomi:</b> {channel.channel_name}
🆔 <b>ID:</b> <code>{channel.channel_id}</code>
🎯 <b>Gift olish limiti:</b> {channel.gift_limit if channel.gift_limit is not None else '♾️ Chegaralanmagan'}

━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 Bu kanalga avtomatik giftlar yuboriladi
⚙️ Sozlamalarni o'zgartirish yoki kanalni boshqarish uchun tugmalardan foydalaning"""

        # Tugmalar
        buttons = [
            [
                InlineKeyboardButton("🗑️ Kanalni o'chirish", callback_data=f"delete_{chnl_id}"),
                InlineKeyboardButton("⬅️ Ortga", callback_data="back_channels")
            ]
        ]

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )

    except Channels.DoesNotExist:
        await query.message.edit_text(
            "❌ <b>Kanal topilmadi!</b>\n\n"
            "🔍 Kanal o'chirilgan yoki mavjud emas.\n"
            "⬅️ Orqaga qaytish uchun /channels buyrug'ini bosing.",
            parse_mode="HTML"
        )
    except Exception as e:
        await query.message.edit_text(
            f"⚠️ <b>Xato yuz berdi!</b>\n\n"
            f"🚨 <b>Xatolik:</b> <code>{e}</code>\n\n"
            f"🔄 Iltimos, qayta urinib ko'ring yoki qo'llab-quvvatlash bilan bog'laning.",
            parse_mode="HTML"
        )
