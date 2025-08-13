import logging
from database.db import get_default_users

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def send_gift_notification(context, gift):
    users = await get_default_users()
    sent_count = 0
    for user in users:
        message_text = (
            f"🎉 Yangi va sizga mos Star Gift topildi!\n\n"
            f"⭐ Narxi: {gift.stars} Stars\n"
            f"⏳ Chiqqan sana: {gift.first_sale_date}\n"
        )
        
        try:
            await context.bot.send_sticker(user.telegram_id, gift.sticker_path)
            await context.bot.send_message(user.telegram_id, message_text)
            logger.info(f"📱 Foydalanuvchi {user.telegram_id} ga gift notification yuborildi")
            sent_count += 1
        except Exception as e:
            logger.error(f"❌ Gift notification yuborishda xato: {e}")

    if sent_count > 0:
        return True
    else:
        return False