import asyncio
import logging

from database.models import User, Channels
from database.db import deduct_stars, create_transaction, add_stars

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def process_single_request(context, gift_data):
    premium_users = get_premium_users(gift_data)
    premium_channels = get_premium_channels(gift_data)
    
    successful_sends = 0
    insufficient_balance_users = 0
    
    try:
        user_tasks = []
        for user in premium_users:
            task = process_user_gift_safe(context, user, gift_data)
            user_tasks.append(task)
        
        channel_tasks = []
        for channel in premium_channels:
            task = process_channel_gift_safe(context, channel, gift_data)
            channel_tasks.append(task)
        
        all_tasks = user_tasks + channel_tasks
        
        if not all_tasks:
            logger.info("ℹ️ Hech qanday premium user yoki kanal topilmadi")
            return
        
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        for i, result in enumerate(results[:len(user_tasks)]):
            user = premium_users[i]
            
            if isinstance(result, Exception):
                logger.error(f"❌ User {user.telegram_id} da kutilmagan xato: {result}")
            elif result == "success":
                successful_sends += 1
                logger.info(f"✅ User {user.telegram_id} ga muvaffaqiyatli yuborildi")
            elif result == "insufficient_balance":
                insufficient_balance_users += 1
                logger.info(f"💰 User {user.telegram_id} da balans yetarli emas")
            elif result == "failed":
                logger.warning(f"⚠️ User {user.telegram_id} ga yuborishda xato")
        
        for i, result in enumerate(results[len(user_tasks):]):
            channel = premium_channels[i]
            
            if isinstance(result, Exception):
                logger.error(f"❌ Channel {channel.channel_name} da kutilmagan xato: {result}")
            elif result == "success":
                successful_sends += 1
                logger.info(f"✅ Channel {channel.channel_name} ga muvaffaqiyatli yuborildi")
            elif result == "insufficient_balance":
                insufficient_balance_users += 1
                logger.info(f"💰 Channel {channel.channel_name} uchun balans yetarli emas")
            elif result == "failed":
                logger.warning(f"⚠️ Channel {channel.channel_name} ga yuborishda xato")

        logger.info(f"📊 Gift {gift_data['id']} natijasi: {successful_sends} muvaffaqiyatli, {insufficient_balance_users} balans yetarli emas")

    except Exception as e:
        logger.error(f"❌ Parallel processing da xato: {e}", exc_info=True)

# ========== USER PROCESSING ==========

async def process_user_gift_safe(context, user, gift_data):
    try:
        return await process_user_gift(context, user, gift_data)
    except Exception as e:
        logger.error(f"❌ User {user.telegram_id} ga gift yuborishda xato: {e}", exc_info=True)
        return "failed"

async def process_user_gift(context, user, gift_data):
    stars_per_gift = int(gift_data['stars'])
    gift_id = gift_data['id']
    user_stars = int(user.stars)

    if user_stars < stars_per_gift:
        await send_insufficient_balance_message_user(context, user, gift_data)
        return "insufficient_balance"

    if not await deduct_stars(user.telegram_id, stars_per_gift):
        logger.error(f"❌ User {user.telegram_id} hisobidan Stars ayirib bo'lmadi")
        await create_transaction(
            user_id=user.telegram_id,
            status='FAILED_DEDUCT',
            stars=stars_per_gift,
            gift_id=gift_id,
            description="User uchun gift sotib olishda Stars ayirishda xato"
        )
        return "failed"

    try:
        sent_count = 0
        
        while True:
            if user.gift_limit is not None and sent_count >= user.gift_limit:
                break
                
            if user.stars < stars_per_gift:
                break

            # Gift yuborish
            await context.bot.send_gift(chat_id=user.telegram_id, gift_id=gift_id)
            
            sent_count += 1
            user.stars -= stars_per_gift
            user.save()
            
            await create_transaction(
                user_id=user.telegram_id,
                gift_id=gift_id,
                status='PURCHASED',
                stars=stars_per_gift,
                description=f"User ga {sent_count} ta gift muvaffaqiyatli yuborildi"
            )

            logger.info(f"✅ Gift {gift_id} user {user.telegram_id} ga yuborildi ({sent_count}-marta)")

    except Exception as send_e:
        error_msg = str(send_e).lower()
        
        if 'stargift_usage_limited' in error_msg or 'limit' in error_msg:
            logger.warning(f"⚠️ User {user.telegram_id}: Gift limit yetdi yoki tugadi")
        else:
            logger.error(f"❌ User {user.telegram_id} ga giftni yuborishda xato: {send_e}")
        
        reverted = await add_stars(user.telegram_id, stars_per_gift)
        status = 'FAILED_REVERTED' if reverted else 'FAILED_NO_REVERT'
        description = "User ga gift yuborishda xato, Stars " + ("qaytarildi" if reverted else "qaytarishda ham xato")
        
        await create_transaction(
            user_id=user.telegram_id,
            status=status,
            stars=stars_per_gift,
            gift_id=gift_id,
            description=description
        )
        return "failed"

# ========== CHANNEL PROCESSING ==========

async def process_channel_gift_safe(context, channel, gift_data):
    try:
        return await process_channel_gift(context, channel, gift_data)
    except Exception as e:
        logger.error(f"❌ Channel {channel.channel_name} ga gift yuborishda xato: {e}", exc_info=True)
        return "failed"

async def process_channel_gift(context, channel, gift_data):
    stars_per_gift = int(gift_data['stars'])
    gift_id = gift_data['id']
    
    owner = channel.user
    owner_stars = int(owner.stars)

    if owner_stars < stars_per_gift:
        await send_insufficient_balance_message_channel(context, channel, gift_data)
        return "insufficient_balance"

    try:
        sent_count = 0
        
        while True:
            if owner.gift_limit is not None and sent_count >= owner.gift_limit:
                break
                
            if not await deduct_stars(owner.telegram_id, stars_per_gift):
                break
                
            try:
                await context.bot.send_gift(chat_id=channel.channel_id, gift_id=gift_id)
                sent_count += 1
                await create_transaction(
                user_id=owner.telegram_id,
                gift_id=gift_id,
                status='PURCHASED',
                stars=stars_per_gift,
                description=f"Channel {channel.channel_name} ga {sent_count}-marta gift muvaffaqiyatli yuborildi"
            )
            except Exception as e:
                # Stars qaytarish
                await add_stars(owner.telegram_id, stars_per_gift)
                raise e

    except Exception as send_e:
        error_msg = str(send_e).lower()
        
        # Rate limit handle
        if 'stargift_usage_limited' in error_msg or 'limit' in error_msg:
            logger.warning(f"⚠️ Channel {channel.channel_name}: Gift limit yetdi yoki tugadi")
        else:
            logger.error(f"❌ Channel {channel.channel_name} ga giftni yuborishda xato: {send_e}")
        
        # Stars qaytarish
        status = 'FAILED_REVERTED' 
        description = f"Channel {channel.channel_name} ga gift yuborishda xato"
        
        await create_transaction(
            user_id=owner.telegram_id,
            status=status,
            stars=stars_per_gift,
            gift_id=gift_id,
            description=description
        )
        return "failed"

# ========== HELPER FUNCTIONS ==========

def get_premium_users(gift):
    """Send_to 'user' yoki 'user_and_channel' bo'lgan premium userlar"""
    return User.select().where(
        (User.is_premium == True) &
        (User.min_stars.is_null(False)) &
        (User.max_stars.is_null(False)) &
        (User.is_monitoring_active == True) &
        (User.min_stars <= gift['stars']) &
        (User.max_stars >= gift['stars']) &
        (User.send_to.in_(['user', 'user_and_channel'])) &
        ((User.gift_limit.is_null()) | (User.gift_limit > 0))  # Limit yo'q yoki 0 dan katta
    )

def get_premium_channels(gift):
    """Premium userlarning kanallarini olish"""
    premium_users_with_channels = User.select().where(
        (User.is_premium == True) &
        (User.min_stars.is_null(False)) &
        (User.max_stars.is_null(False)) &
        (User.is_monitoring_active == True) &
        (User.min_stars <= gift['stars']) &
        (User.max_stars >= gift['stars']) &
        (User.send_to.in_(['channel', 'user_and_channel']))
    )
    
    channels = []
    for user in premium_users_with_channels:
        user_channels = Channels.select().where(
            (Channels.user == user) &
            ((Channels.gift_limit.is_null()) | (Channels.gift_limit > 0)) 
        )
        channels.extend(list(user_channels))
    
    return channels

async def send_insufficient_balance_message_user(context, user, gift):
    """User uchun balans yetarli emas xabari"""
    message_text = (
        f"❗ Sizga mos Star Gift topildi, ammo Stars balansingiz yetarli emas!\n\n"
        f"🎁 Emoji: {gift['alt'] or 'Nomsiz'}\n"
        f"⭐ Narxi: {gift['stars']} Stars\n"
        f"👤 Target: Siz (User)\n"
        f"💰 Sizning balansingiz: {user.stars} Stars\n"
        f"💎 Yetishmayotgan: {int(gift['stars']) - user.stars} Stars\n\n"
        f"⚡ Tezroq to'ldiring - boshqa foydalanuvchilar ham kutmoqda!\n"
        f"Iltimos, balansingizni to'ldiring: /donate"
    )
    
    try:
        await context.bot.send_message(user.telegram_id, message_text)
        logger.info(f"💰 User {user.telegram_id} ga insufficient balance xabari yuborildi")
        return True
    except Exception as e:
        logger.error(f"❌ User insufficient balance xabar yuborishda xato: {e}")
        return False

async def send_insufficient_balance_message_channel(context, channel, gift):
    """Channel uchun balans yetarli emas xabari"""
    owner = channel.user
    
    message_text = (
        f"❗ Sizning kanalingizga mos Star Gift topildi, ammo Stars balansingiz yetarli emas!\n\n"
        f"🎁 Emoji: {gift['alt'] or 'Nomsiz'}\n"
        f"⭐ Narxi: {gift['stars']} Stars\n"
        f"📺 Kanal: {channel.channel_name}\n"
        f"💰 Sizning balansingiz: {owner.stars} Stars\n"
        f"💎 Yetishmayotgan: {int(gift['stars']) - owner.stars} Stars\n\n"
        f"⚡ Tezroq to'ldiring - boshqa foydalanuvchilar ham kutmoqda!\n"
        f"Iltimos, balansingizni to'ldiring: /donate"
    )
    
    try:
        await context.bot.send_message(owner.telegram_id, message_text)
        logger.info(f"💰 Channel {channel.channel_name} owner ga insufficient balance xabari yuborildi")
        return True
    except Exception as e:
        logger.error(f"❌ Channel insufficient balance xabar yuborishda xato: {e}")
        return False