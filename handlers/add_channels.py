from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User, Channels

GET_USER, GET_CHANNEL_NAME, GET_CHANNEL_ID = range(3)

async def cancel_command(update, context):
    await update.message.reply_text(
        "❌ <b>Jarayon to'xtatildi!</b>\n\n"
        "🔄 Bosh menuga qaytish uchun /start buyrug'ini bosing.",
        parse_mode="HTML"
    )
    return ConversationHandler.END

async def get_user(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    await context.bot.send_message(
        text="📝 <b>Kanal nomini kiriting:</b>\n\n"
             "💡 <b>Misol:</b> Mening Kanalim\n"
             "📝 <b>Qoidalar:</b>\n"
             "   • Aniq va tushunarli nom bering\n"
             "   • 50 belgidan oshmasin\n\n"
             "❌ Bekor qilish uchun: /cancel",
        chat_id=user_id,
        parse_mode="HTML"
    )
    return GET_USER

async def get_channel_name(update, context):
    msg = update.message.text
    
    if len(msg) > 50:
        await update.message.reply_text(
            "⚠️ <b>Kanal nomi juda uzun!</b>\n\n"
            "📏 Maksimal 50 belgi bo'lishi kerak.\n"
            "📝 Iltimos, qisqaroq nom kiriting:",
            parse_mode="HTML"
        )
        return GET_USER
    
    context.user_data['channel_name'] = msg
    await update.message.reply_text(
        "🆔 <b>Kanal ID sini kiriting:</b>\n\n"
        "📋 <b>ID olish yo'li:</b>\n"
        "   1️⃣ @userinfobot ga kanalingizdagi istalgan matnli xabarni forward qiling\n"
        "   2️⃣ Yoki kanal sozlamalaridan ID ni ko'ring\n\n"
        "💡 <b>Misol:</b> <code>-1001234567890</code>\n"
        "⚠️ <b>Muhim:</b> ID <code>-100</code> bilan boshlanishi kerak!\n\n"
        "❌ Bekor qilish uchun: /cancel",
        parse_mode="HTML"
    )
    return GET_CHANNEL_NAME

async def get_channel_id(update, context):
    msg = update.message.text
    
    if msg.startswith('-100') and len(msg) > 4 and msg[4:].isdigit():
        context.user_data['channel_id'] = msg
        await update.message.reply_text(
            "🎯 <b>Gift qabul qilish limitini kiriting:</b>\n\n"
            "🔢 <b>Raqam kiriting:</b> Masalan, 10, 50, 100\n"
            "♾️ <b>Limitsiz uchun:</b> Faqat <code>.</code> belgisini kiriting\n"
            "❌ Bekor qilish uchun: /cancel",
            parse_mode="HTML"
        )
        return GET_CHANNEL_ID
    else:
        await update.message.reply_text(
            "❌ <b>Xatolik: ID noto'g'ri!</b>\n\n"
            "🔍 <b>To'g'ri format:</b>\n"
            "   • <code>-100</code> bilan boshlanishi kerak\n"
            "   • Faqat raqamlardan iborat bo'lishi kerak\n\n"
            "💡 <b>To'g'ri misol:</b> <code>-1001234567890</code>\n"
            "❌ <b>Noto'g'ri misol:</b> <code>@kanal_nomi</code>\n\n"
            "🔄 Iltimos, to'g'ri ID kiriting:",
            parse_mode="HTML"
        )
        return GET_CHANNEL_NAME

async def save_channel(update, context):
    msg = update.message.text
    user_id = update.effective_user.id
    channel_name = context.user_data['channel_name']
    channel_id = context.user_data['channel_id']

    if msg.isdigit() or msg == ".":
        try:
            user = User.get(telegram_id=user_id)

            # Kanal allaqachon mavjudligini tekshirish
            existing_channel = Channels.get_or_none(
                (Channels.user == user) & (Channels.channel_id == channel_id)
            )
            
            if existing_channel:
                await update.message.reply_text(
                    "⚠️ <b>Bu kanal allaqachon qo'shilgan!</b>\n\n"
                    "🔄 Boshqa kanal ID sini kiriting yoki /cancel buyrug'ini bosing.",
                    parse_mode="HTML"
                )
                return GET_CHANNEL_NAME

            Channels.create(
                user=user,
                channel_name=channel_name,
                channel_id=channel_id,
                gift_limit=int(msg) if msg != "." else None
            )
            
            back_btn = [[InlineKeyboardButton(text='⬅️ Kanallar ro\'yxatiga qaytish', callback_data='back_channels')]]
            
            limit_text = f"{msg} ta gift" if msg != "." else "♾️ Limitsiz"
            
            await update.message.reply_text(
                f"✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
                f"📺 <b>Nomi:</b> {channel_name}\n"
                f"🆔 <b>ID:</b> <code>{channel_id}</code>\n"
                f"🎯 <b>Gift limiti:</b> {limit_text}\n\n"
                f"🎁 <b>Endi bu kanalga avtomatik giftlar yuboriladi!</b>\n"
                f"⚙️ Sozlamalarni o'zgartirish uchun /channels buyrug'ini ishlatishingiz mumkin.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(back_btn)
            )
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ <b>Xatolik yuz berdi!</b>\n\n"
                f"🚨 <b>Sabab:</b> <code>{str(e)}</code>\n\n"
                f"🔄 Iltimos, qayta urinib ko'ring yoki /cancel buyrug'ini bosing.",
                parse_mode="HTML"
            )
            return GET_CHANNEL_ID
    else:
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "🔢 <b>Faqat raqam yoki</b> <code>.</code> <b>belgisini kiriting</b>\n\n"
            "💡 <b>To'g'ri misollar:</b>\n"
            "   • <code>10</code> - 10 tagacha gift\n"
            "   • <code>50</code> - 50 tagacha gift\n"
            "   • <code>.</code> - limitsiz\n\n"
            "🔄 Iltimos, qayta kiriting:",
            parse_mode="HTML"
        )
        return GET_CHANNEL_ID

# Conversation handler
add_channel_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(get_user, pattern="add_channel")],
    states={
        GET_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_name)],
        GET_CHANNEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_id)],
        GET_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_channel)]
    },
    fallbacks=[CommandHandler('cancel', cancel_command)],
    per_user=True
)