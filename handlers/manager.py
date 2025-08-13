from database.models import User
from telegram import BotCommand, BotCommandScopeChat
from config import MANAGER_ID, MANAGER_USERNAME

# Premium foydalanuvchi uchun buyruqlar ro'yxati
async def set_commands(application, chat_id):
    await application.bot.set_my_commands(
        [
            BotCommand("start", "🚀 Botni ishga tushirish"),
            BotCommand("help", "ℹ️ Yordam olish"),
            BotCommand("donate", "💰 Hisobni to'ldirish"),
            BotCommand("refund", "💳 Stars yechish"),
            BotCommand("start_process", "🎯 Gift kuzatuvini boshlash"),
            BotCommand("stop_process", "🛑 Gift kuzatuvini to'xtatish"),
            BotCommand("info", "⚙️ Sozlamalar haqida ma'lumot"),
            BotCommand("channels", "📢 Kanallarni boshqarish"),
        ],
        scope=BotCommandScopeChat(chat_id)
    )

# Manager callback tugmalari
async def manager_callback(update, context):
    query = update.callback_query
    data_sp = query.data.split('_')
    user_id = int(data_sp[1])
    user = User.get_or_none(telegram_id=user_id)

    await query.answer()

    if data_sp[0] == 'approve':
        if not user:
            await context.bot.send_message(
                MANAGER_ID, 
                "⚠️ <b>Xatolik:</b> Bunday foydalanuvchi topilmadi!",
                parse_mode="HTML"
            )
            return
        
        # Premium berish
        user.is_premium = True
        user.save()

        await query.message.delete()

        await context.bot.send_message(
            MANAGER_ID,
            f"✅ <b>{user.first_name}</b> premium foydalanuvchi qilindi!",
            parse_mode="HTML"
        )

        await context.bot.send_message(
            user_id,
            "🎉 <b>Tabriklaymiz!</b>\n"
            "Siz endi <b>Premium foydalanuvchi</b> bo'ldingiz! 🏆\n\n"
            "🔹 Yangi imkoniyatlar siz uchun ochildi.\n"
            "ℹ️ Qo'shimcha ma'lumot olish uchun /help buyrug'ini bosing.",
            parse_mode="HTML"
        )

        await set_commands(context.application, user_id)

    elif data_sp[0] == 'reject':
        await query.message.delete()

        await context.bot.send_message(
            MANAGER_ID,
            f"❌ <b>{user.first_name}</b> premium so'rovi rad etildi.",
            parse_mode="HTML"
        )

        await context.bot.send_message(
            user_id,
            f"⚠️ Premium so'rovingiz rad etildi.\n\n"
            f"Agar bu xato bo'lsa, iltimos <b>Manager</b> ({MANAGER_USERNAME}) bilan bog'laning.",
            parse_mode="HTML"
        )
