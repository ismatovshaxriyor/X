from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Channels

async def delete_channel_callback(update, context):
    query = update.callback_query
    await query.answer()

    try:
        # Kanal ID ni olish
        _, channel_id = query.data.split('_', 1)

        # Kanalni topish
        channel = Channels.get(Channels.channel_id == channel_id)
        channel_name = channel.channel_name

        # Kanalni o‘chirish
        channel.delete_instance()

        # Ortga qaytish tugmasi
        back_btn = [[InlineKeyboardButton("🔙 Ortga qaytish", callback_data="back_channels")]]
        reply_markup = InlineKeyboardMarkup(back_btn)

        await query.message.edit_text(
            f"✅ <b>{channel_name}</b> kanali muvaffaqiyatli o‘chirildi!",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    except Channels.DoesNotExist:
        await query.message.edit_text("❌ Bunday kanal topilmadi!")
    except Exception as e:
        await query.message.edit_text(f"❌ Xatolik yuz berdi:\n<code>{e}</code>", parse_mode="HTML")
