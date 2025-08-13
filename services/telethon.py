import asyncio
import os
import logging
from telethon.sync import TelegramClient
from telethon.tl.functions.payments import GetStarGiftsRequest
from telethon.tl.types import Document
from telethon.errors import FloodWaitError, RPCError

from config import API_HASH, API_ID, PHONE_NUMBER
from database.models import Gift, User
from handlers.gift_sender import process_single_request
from database.db import get_new_gift
from handlers.notification_sender import send_gift_notification

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 100
FLOOD_WAIT_MAX = 300


class TelegramGiftMonitor:
    def __init__(self, api_id, api_hash, phone_number, bot):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = None
        self.last_gifts_hash = 0 
        self.bot = bot 

    async def _connect(self):
        logger.info("🔌 Telegram userbot ulanishga harakat qilmoqda...")
        self.client = TelegramClient(
            'userbot_session',
            self.api_id,
            self.api_hash,
        )
        try:
            await self.client.start(phone=self.phone_number)
            logger.info("✅ Telegram userbot muvaffaqiyatli ulandi!")
        except Exception as e:
            logger.critical(f"🔴 Userbot ulanishda xato: {e}", exc_info=True)
            raise

    def _get_gift_attribute(self, gift_tl, attributes):
        for attr in attributes:
            if hasattr(gift_tl, attr):
                return getattr(gift_tl, attr)
        return None

    async def _get_gifts(self):
        logger.info("🔍 Yangi giftlar uchun Telegram API tekshirilmoqda...")
        try:
            gifts_response = await self.client(GetStarGiftsRequest(hash=self.last_gifts_hash))
            try:
                gifts = gifts_response.gifts
                logger.info("✅ Gifts ro'yxati muvaffaqiyatli olindi")
                
                if not gifts:
                    logger.info("ℹ️ Gift ro'yxati bo'sh - yangi giftlar yo'q")
                    return
                
                for gift_tl in gifts:
                    try:
                        sticker_id = gift_tl.sticker.id
                        access_hash = gift_tl.sticker.access_hash
                        file_reference = gift_tl.sticker.file_reference
                        date = gift_tl.sticker.date
                        alt = gift_tl.sticker.attributes[1].alt
                        mime_type = gift_tl.sticker.mime_type
                        size = gift_tl.sticker.size
                        dc_id = gift_tl.sticker.dc_id
                        gift_id = gift_tl.id
                        stars = self._get_gift_attribute(gift_tl, ['stars'])
                        limited = self._get_gift_attribute(gift_tl, ['limited'])
                        sold_out = self._get_gift_attribute(gift_tl, ['sold_out'])
                        first_sale_date = self._get_gift_attribute(gift_tl, ['first_sale_date'])
                        last_sale_date = self._get_gift_attribute(gift_tl, ['last_sale_date'])
                        availability_remains = self._get_gift_attribute(gift_tl, ['availability_remains'])

                        if gift_id is None:
                            logger.warning(f"⚠️ Gift ID topilmadi, o'tkazib yuborildi: {gift_tl}")
                            continue

                        gift_info = {
                            'id': gift_id,
                            'stars': stars,
                            'limited': limited,
                            'sold_out': sold_out,
                            'first_sale_date': first_sale_date,
                            'last_sale_date': last_sale_date,
                            'date': date,
                            'alt': alt
                        }

                        sticker_info = {
                            'id': sticker_id,
                            'access_hash': access_hash,
                            'file_reference': file_reference,
                            'date': date,
                            'mime_type': mime_type,
                            'size': size,
                            'dc_id': dc_id
                        }
                        await self.process_gift_data(sticker_info, gift_info)

                        gift_obj = await get_new_gift(gift_id)
                        if gift_obj is not None:
                            logger.info(f'Yangi gift topildi! {gift_obj.id}')
                            await process_single_request(self.bot, gift_info)
                            await send_gift_notification(self.bot, gift_obj)

                            gift_obj.status = 'old'
                            gift_obj.save()
                        logger.info(f"🔍 Gift ma'lumotlari - ID: {gift_id}, Stars: {stars}, Availability_remains: {availability_remains}, Alt: {alt}")

                    except Exception as gift_error:
                        logger.error(f"❌ Gift ({gift_tl}) ishlov berishda xato: {gift_error}", exc_info=True)

            except AttributeError as e:
                    logger.info(f"ℹ️ Javobda 'gifts' atributi yo'q - yangilanish yo'q yoki boshqa javob turi. Xato: {e}")
                    return

        except FloodWaitError as e:
            wait_time = min(e.seconds + 5, FLOOD_WAIT_MAX)
            logger.warning(f"⏳ FloodWaitError! {wait_time} soniya kutilmoqda. Xato: {e}")
            await asyncio.sleep(wait_time)
        except RPCError as e:
            logger.error(f"❌ Telethon RPC xatosi: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"❌ Kutilmagan xato: {e}", exc_info=True)

    async def process_gift_data(self, sticker_data, gift_data):
        sticker_document = Document(
            id=sticker_data['id'],
            access_hash=sticker_data['access_hash'],
            file_reference=sticker_data['file_reference'],
            date=sticker_data['date'],
            mime_type=sticker_data['mime_type'],
            size=sticker_data['size'],
            dc_id=sticker_data['dc_id'],
            attributes=[]
        )

        try:
            file_name = f"stickers/stiker_{sticker_data['id']}.tgs"
            
            # Fayl mavjudligini tekshirish
            if os.path.exists(file_name):
                print(f"Fayl '{file_name}' allaqachon mavjud, yuklanmaydi.")
                file_path = file_name
            else:
                # Papka mavjud emasligini tekshirish va yaratish
                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                
                print(f"Stiker yuklanmoqda: {file_name}")
                file_path = await self.client.download_media(sticker_document, file=file_name)
                print(f"Stiker '{file_path}' manziliga muvaffaqiyatli yuklab olindi.")
            
            # Ma'lumotlarni bazaga saqlash
            Gift.insert(
                id=gift_data['id'],
                sticker_path=file_path,
                stars=gift_data['stars'],
                limited=gift_data['limited'],
                status='new',
                sold_out=gift_data['sold_out'],
                first_sale_date=gift_data['first_sale_date'],
                last_sale_date=gift_data['last_sale_date']
            ).on_conflict(
                conflict_target=[Gift.id],
                preserve=[Gift.sticker_path, Gift.stars, Gift.limited, Gift.sold_out, Gift.first_sale_date, Gift.last_sale_date],
                update={'sticker_path': file_path, 'stars': gift_data['stars']}
            ).execute()
            
            print("Ma'lumotlar Gift modeliga muvaffaqiyatli saqlandi/yangilandi.")
            
        except FileNotFoundError:
            print(f"Xato: '{os.path.dirname(file_name)}' papkasi yaratilmadi.")
        except PermissionError:
            print(f"Xato: '{file_name}' faylini yaratish uchun ruxsat yo'q.")
        except Exception as e:
            print(f"Stikerni yuklash yoki saqlashda xato yuz berdi: {e}")





async def main_userbot(bot):
    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        logger.critical("🔴 Muhit o'zgaruvchilari (API_ID, API_HASH, PHONE_NUMBER) to'liq emas. Iltimos, config.py faylini tekshiring.")
        return
    
    monitor = TelegramGiftMonitor(API_ID, API_HASH, PHONE_NUMBER, bot)
    
    try:
        await monitor._connect()
        logger.info(f"🚀 Userbot doimiy kuzatish rejimida ishga tushdi. Har {CHECK_INTERVAL_SECONDS} soniyada tekshiradi.")
        while True:
            try:
                active_monitoring_users = User.select().where(User.is_monitoring_active == True).count()
                if active_monitoring_users >= 0:
                    await monitor._get_gifts()
                    logger.info(f"💤 Keyingi tekshirish uchun {CHECK_INTERVAL_SECONDS} soniya kutilmoqda...")
                    await asyncio.sleep(CHECK_INTERVAL_SECONDS)
                else:
                    logger.info("ℹ️ Monitoring faol bo'lgan foydalanuvchilar topilmadi. 3 soniya kutilmoqda...")
                    await asyncio.sleep(3)
            except Exception as loop_error:
                logger.error(f"❌ Userbot asosiy tsiklida xato: {loop_error}", exc_info=True)
                await asyncio.sleep(5)
    except FloodWaitError as e:
        logger.warning(f"FloodWaitError: {e.seconds} soniya kutilmoqda...")
        await asyncio.sleep(e.seconds)
    except RPCError as e:
        logger.error(f"Telegram RPC xatosi: {e}", exc_info=True)
    except Exception as e:
        logger.critical(f"Kutilmagan xato: {e}", exc_info=True)
    finally:
        if monitor.client and monitor.client.is_connected():
            await monitor.client.disconnect()
            logger.info("Userbot o'chirildi.")