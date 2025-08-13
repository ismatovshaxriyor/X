from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import LabeledPrice

from database.models import User, Payment, Channels
from database.db import get_user
from config import MANAGER_ID, MANAGER_USERNAME
from .chech_agree_dec import require_agreement


async def start_command(update, context):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    
    user, created = User.get_or_create(
        telegram_id=user_id,
        defaults={'username': username, "first_name": first_name}
    )

    text = f"""🎁 <b>Salom {first_name}!</b>

🌟 Siz bu bot orqali yangi chiqayotgan <b>Gift</b>lar haqida ma'lumot olishingiz mumkin.

📋 To'liq ma'lumot olish uchun /help buyrug'ini bosing."""
    
    await update.message.reply_text(text, parse_mode="HTML")

async def help_command(update, context):
    user_id = update.effective_user.id

    text_for_premium_user = """🎯 <b>Premium Foydalanuvchi uchun yo'riqnoma</b>

🤖 Bot sizga avtomatik <b>Gift</b>larni olib beradi, buning uchun quyidagi qadamlarni bajaring:

<b>1️⃣ Gift oralig'ini va limitini belgilang:</b>
    <code>/set_gift_prefs &lt;minimal qiymat&gt; &lt;maksimal qiymat&gt; &lt;limit&gt;</code>

<b>2️⃣ Hisobingizni to'ldiring:</b>
    <code>/donate &lt;miqdori&gt;</code>

<b>3️⃣ Giftlarni kuzatishni ishga tushuring:</b>
    <code>/start_process</code>

━━━━━━━━━━━━━━━━━━━━━━━━━

📋 <b>Qo'shimcha buyruqlar:</b>
🛑 Kuzatishni to'xtatish - /stop_process
👤 Akkount haqida ma'lumot - /info
📺 Kanallar boshqaruvi - /channels
💰 To'lovni qaytarish - /refund"""

    text_for_default_user = """🎁 <b>Bepul foydalanuvchi uchun</b>

📢 Bot yangi <b>Gift</b> chiqqanida sizga xabar beradi.

⭐ Agar ularni avtomatik olib berish xizmatidan foydalanmoqchi bo'lsangiz /premium buyrug'ini bosing.

💎 Premium obuna sizga quyidagilarni beradi:
   • 🤖 Avtomatik gift olish
   • ⚙️ Sozlamalarni boshqarish
   • 📊 Batafsil statistika
   • 🏆 Ustuvorlik"""

    user = await get_user(user_id)

    if user:
        if user.is_premium:
            await update.message.reply_text(text_for_premium_user, parse_mode="HTML")
        else:
            await update.message.reply_text(text_for_default_user, parse_mode="HTML")
    else:
        await update.message.reply_text('❌ <b>Siz ro\'yxatdan o\'tmagansiz!</b>\n\n🔥 Iltimos /start buyrug\'ini bosib ro\'yxatdan o\'ting', parse_mode="HTML")

@require_agreement
async def premium_command(update, context):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name

    buttons_for_manager = [
        [InlineKeyboardButton(text='✅ Tasdiqlash', callback_data=f'approve_{user_id}')],
        [InlineKeyboardButton(text='❌ Rad etish', callback_data=f'reject_{user_id}')]
    ]

    user = await get_user(user_id)

    if user:
        if user.is_premium:
            await update.message.reply_text('🎉 <b>Tabriklaymiz!</b>\n\n⭐ Siz allaqachon <b>Premium</b> obunachisiz!', parse_mode="HTML")
            return
        else:
            await update.message.reply_text(f"""📤 <b>Premium so'rov yuborildi!</b>

⏳ Sizning premium so'rovingiz managerga yuborildi.

👨‍💼 Manager: {MANAGER_USERNAME}

💰 Manager bilan bog'lanib, to'lovni amalga oshirgach, manager sizning so'rovingizni tasdiqlaydi.

⚡ So'rov holati haqida xabardor bo'lib turasiz!""", parse_mode="HTML")
            
            await context.bot.send_message(
                chat_id=MANAGER_ID, 
                text=f"""🔔 <b>Yangi Premium So'rov!</b>

👤 <b>Foydalanuvchi:</b> {first_name}
🆔 <b>User ID:</b> <code>{user_id}</code>

⚡ Harakatni tanlang:""", 
                reply_markup=InlineKeyboardMarkup(buttons_for_manager),
                parse_mode="HTML"
            )
    else:
        await update.message.reply_text("❌ <b>Siz ro'yxatdan o'tmagansiz!</b>\n\n🚀 Iltimos /start buyrug'ini bosib ro'yxatdan o'ting!", parse_mode="HTML")

async def set_gift_prefs_command(update, context):
    user_id = update.effective_user.id
    
    if 2 > len(context.args) or len(context.args) > 3:
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "📝 Iltimos, kamida ikkita raqam kiriting:\n"
            "💡 <b>Misol:</b> <code>/set_gift_prefs 100 500</code>\n\n"
            "🔢 <b>Format:</b> <code>/set_gift_prefs [min] [max] [limit]</code>",
            parse_mode="HTML"
        )
        return

    try:
        gift_limit = None
        if len(context.args) == 2:
            min_stars = int(context.args[0])
            max_stars = int(context.args[1])
        else:
            min_stars = int(context.args[0])
            max_stars = int(context.args[1])
            gift_limit = int(context.args[2])

        if max_stars < min_stars:
            await update.message.reply_text(
                "⚠️ <b>Xatolik!</b>\n\n"
                "📊 Iltimos, to'g'ri minimal va maksimal stars qiymatlarini kiriting.\n"
                "🔢 Minimal qiymat maksimaldan kichik bo'lishi kerak!",
                parse_mode="HTML"
            )
            return

        user = User.get_or_none(telegram_id=user_id)
        user.min_stars = min_stars
        user.max_stars = max_stars
        user.gift_limit = gift_limit
        user.save()

        if len(context.args) == 2:
            await update.message.reply_text(
                f"✅ <b>Sozlamalar saqlandi!</b>\n\n"
                f"⭐ <b>Minimal stars:</b> {min_stars}\n"
                f"🌟 <b>Maksimal stars:</b> {max_stars}\n\n"
                f"🎯 Endi siz {min_stars}-{max_stars} orasidagi giftlarni olasiz!",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                f"✅ <b>Sozlamalar saqlandi!</b>\n\n"
                f"⭐ <b>Minimal stars:</b> {min_stars}\n"
                f"🌟 <b>Maksimal stars:</b> {max_stars}\n"
                f"🎁 <b>Gift limiti:</b> {gift_limit}\n\n"
                f"🎯 Endi siz {min_stars}-{max_stars} orasidagi giftlarni olasiz!",
                parse_mode="HTML"
            )

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "🔢 Iltimos, faqat raqam kiriting.\n"
            "💡 <b>Misol:</b> <code>/set_gift_prefs 100 500</code>",
            parse_mode="HTML"
        )

async def send_stars_invoice(update, context):
    chat_id = update.effective_chat.id
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "💰 Iltimos, yulduzlar miqdorini kiriting.\n"
            "💡 <b>Misol:</b> <code>/donate 500</code>",
            parse_mode="HTML"
        )
        return

    try:
        stars_amount = int(context.args[0])
        if stars_amount <= 0:
            await update.message.reply_text(
                "⚠️ <b>Xatolik!</b>\n\n"
                "🔢 Yulduzlar miqdori noldan katta bo'lishi kerak.\n"
                "💡 <b>Misol:</b> <code>/donate 100</code>",
                parse_mode="HTML"
            )
            return

    except ValueError:
        await update.message.reply_text(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "🔢 Iltimos, faqat raqam kiriting.\n"
            "💡 <b>Misol:</b> <code>/donate 500</code>",
            parse_mode="HTML"
        )
        return
    
    title = f"⭐ {stars_amount} Telegram Stars"
    description = f"💰 Hisobingizni {stars_amount} starsga to'ldirmoqchisiz!"
    payload = f"stars_purchase_{stars_amount}"
    provider_token = ""
    currency = "XTR" 
    
    price_unit = stars_amount
    prices = [LabeledPrice(label=f"⭐ {stars_amount} Yulduz", amount=price_unit)]

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices
    )

    await context.bot.send_message(
        text='💳 <b>To\'lov tafsilotlari yuborildi!</b>\n\n'
             '✅ To\'lovni amalga oshirgach hisobingizni tekshiring!\n'
             '📊 Balans yangilanishi haqida xabardor bo\'lasiz.',
        chat_id=chat_id,
        parse_mode="HTML"
    )

async def start_process_command(update, context):
    user_id = update.effective_user.id

    user = User.get(telegram_id=user_id)
    if (user.min_stars is None or user.max_stars is None) and user.is_premium:
        await update.message.reply_text(
            "⚙️ <b>Sozlamalar to'liq emas!</b>\n\n"
            "📊 Iltimos avval Gift sotib olish oralig'ini belgilang!\n\n"
            "💡 <b>Misol:</b> <code>/set_gift_prefs 100 500</code>",
            parse_mode="HTML"
        )
    elif user.is_premium:
        user.is_monitoring_active = True
        user.save()
        await update.message.reply_text(
            '🚀 <b>Giftlarni kuzatish boshlandi!</b>\n\n'
            '🎁 Yangi gift topilsa avtomatik yuboriladi\n'
            '⚡ Siz belgilagan sozlamalarga mos giftlar olinadi\n\n'
            '🛑 To\'xtatish uchun: /stop_process',
            parse_mode="HTML"
        )

async def stop_process_command(update, context):
    user_id = update.effective_user.id
    user = User.get(telegram_id=user_id)

    if user.is_premium:
        if user.is_monitoring_active == True:
            user.is_monitoring_active = False
            user.save()
            await update.message.reply_text(
                "⏹️ <b>Giftlarni kuzatish to'xtatildi!</b>\n\n"
                "❌ Yangi giftlar chiqsa avtomatik olib berilmaydi\n\n"
                "🚀 Qayta boshlash uchun: /start_process",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "⏸️ <b>Jarayon allaqachon to'xtatilgan!</b>\n\n"
                "🚀 Boshlash uchun: /start_process",
                parse_mode="HTML"
            )

async def info_command(update, context):
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if user:
        if user.is_premium:
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
            
            check_user = "✅" if user.send_to == 'user' else "⚪"
            check_channel = "✅" if user.send_to == 'channel' else "⚪"
            check_channel_and_user = "✅" if user.send_to == 'user_and_channel' else "⚪"
            
            btns = [
                [InlineKeyboardButton(text=f"{check_user} O'zimga", callback_data='sendTo_user'), 
                 InlineKeyboardButton(text=f"{check_channel} Kanallarga", callback_data='sendTo_channel')],
                [InlineKeyboardButton(text=f"{check_channel_and_user} O'zimga va Kanallarga", callback_data='sendTo_userAndChannel')]
            ]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), parse_mode="HTML")

async def refund_payment_command(update, context):
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ <b>To'lov ID si kiritilmagan!</b>\n\n"
                "📝 To'lov ID sini kiriting:\n"
                "💡 <b>Misol:</b> <code>/refund 12345_67890_abcdef</code>",
                parse_mode="HTML"
            )
            return
            
        payment_id = context.args[0]
        user_id = update.effective_user.id

        user = User.get(telegram_id=user_id)
        payment = Payment.get_or_none(
            (Payment.user == user) & (Payment.telegram_payment_charge_id == payment_id)
        )

        if payment:
            user = User.get(telegram_id=user_id)
            
            await update.message.reply_text("⏳ <b>To'lov qaytarilmoqda...</b>\n\n⚡ Iltimos, kuting!", parse_mode="HTML")
            
            result = await context.bot.refund_star_payment(
                user_id=user_id,
                telegram_payment_charge_id=payment_id
            )
            
            if result:
                payment.status = "REFUNDED"
                payment.save()
                user.stars -= payment.amount
                user.save()
                await update.message.reply_text(
                    f"✅ <b>To'lov muvaffaqiyatli qaytarildi!</b>\n\n"
                    f"📄 <b>To'lov ID:</b> <code>{payment_id}</code>\n"
                    f"💰 <b>Miqdor:</b> {payment.amount} ⭐\n"
                    f"📊 <b>Yangi balans:</b> {user.stars} ⭐",
                    parse_mode="HTML"
                )
            else:
                payment.status = "FAILED_REFUNDED"
                payment.save()
                await update.message.reply_text(
                    "❌ <b>To'lovni qaytarishda xatolik!</b>\n\n"
                    "🔄 Iltimos, keyinroq qayta urinib ko'ring yoki qo'llab-quvvatlash bilan bog'laning.",
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text(
                "❌ <b>To'lov topilmadi!</b>\n\n"
                "🔍 Sizda bu ID orqali o'tkazma topilmadi.\n"
                "📝 To'lov ID sini qayta tekshiring.",
                parse_mode="HTML"
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>To'lovni qaytarishda xato!</b>\n\n"
            f"🚨 <b>Xato:</b> <code>{str(e)}</code>\n\n"
            f"🔍 <b>Mumkin bo'lgan sabablar:</b>\n"
            f"• Noto'g'ri to'lov ID\n"
            f"• To'lov allaqachon qaytarilgan\n"
            f"• API xatosi\n"
            f"• Tarmoq muammosi",
            parse_mode="HTML"
        )

async def channels_command(update, context):
    user_id = update.effective_user.id

    user = User.get(telegram_id=user_id)
    try:
        channels = list(Channels.select().where(Channels.user == user))
    except:
        channels = []

    btns = []
    if channels:
        for i, channel in enumerate(channels):
            btn = InlineKeyboardButton(
                text=f'📺 {i+1}. {channel.channel_name}', 
                callback_data=f'chnl_{channel.channel_id}'
            )
            
            if i % 2 == 0: 
                btns.append([btn])  
            else:  
                btns[-1].append(btn) 
        
        btns.append([InlineKeyboardButton(text='➕ Kanal qo\'shish', callback_data='add_channel')])
        await update.message.reply_text(
            '📺 <b>Sizning kanallaringiz:</b>\n\n'
            '🎁 Giftlar shu kanallarga yuboriladi\n'
            '⚙️ Boshqarish uchun kanal nomini bosing',
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="HTML"
        )
    else:
        btns.append([InlineKeyboardButton(text='➕ Kanal qo\'shish', callback_data='add_channel')])
        await update.message.reply_text(
            '📺 <b>Kanallar bo\'limi</b>\n\n'
            '❌ Siz hali kanal qo\'shmadingiz\n\n'
            '💡 Kanal qo\'shib, giftlarni to\'g\'ridan-to\'g\'ri kanallaringizga yuboring!',
            reply_markup=InlineKeyboardMarkup(btns),
            parse_mode="HTML"
        )