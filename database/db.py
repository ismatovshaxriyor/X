from peewee import SqliteDatabase, fn
from config import DATABASE_PATH
from datetime import datetime

db = SqliteDatabase(DATABASE_PATH)

def init_db():
    try:
        from .models import User, Gift, Transactions, Payment, Channels
        db.connect()
        db.create_tables([User, Gift, Transactions, Payment, Channels], safe=True)
        print("Ma'lumotlar bazasi ulandi va jadvallar yaratildi")
    except Exception as e:
        print(f"Ma'lumotlar bazasini ulashda xato: {str(e)}")
        raise

async def add_stars(telegram_id: int, total_stars: int):
    try:
        from .models import User

        user = User.get_or_none(User.telegram_id == telegram_id)
        if user:
            user.stars += total_stars
            user.save()
        else:
            print(f"[!] Foydalanuvchi topilmadi: {telegram_id}")
    except Exception as e:
        print(f"[!] Stars qo'shishda xatolik: {e}")

async def get_total_stars():
    from .models import User
    
    total = User.select(fn.SUM(User.stars)).scalar()
    return total or 0

async def set_user_gift_preferences(telegram_id: int, min_stars: int = None, max_stars: int = None, is_premium: bool = None, is_monitoring_active: bool = None):
    """
    Foydalanuvchining minimal va maksimal Stars qiymatlarini, premium statusini
    va monitoring statusini yangilaydi.
    """
    try:
        from .models import User

        user = User.get_or_none(User.telegram_id == telegram_id)
        if user:
            if min_stars is not None:
                user.min_stars = min_stars
            if max_stars is not None:
                user.max_stars = max_stars
            if is_premium is not None:
                user.is_premium = is_premium
            if is_monitoring_active is not None: # YANGI: monitoring statusini yangilash
                user.is_monitoring_active = is_monitoring_active
            user.save()
            print(f"[DB] Foydalanuvchi {telegram_id} sozlamalari yangilandi: min={user.min_stars}, max={user.max_stars}, premium={user.is_premium}, monitoring={user.is_monitoring_active}")
            return True
        else:
            print(f"[DB] Foydalanuvchi topilmadi: {telegram_id}. Sozlamalarni yangilab bo'lmadi.")
            return False
    except Exception as e:
        print(f"[DB] Foydalanuvchi sozlamalarini yangilashda xatolik: {e}")
        return False

async def get_user(telegram_id: int):
    """Telegram ID bo'yicha foydalanuvchini qaytaradi."""
    from .models import User

    try:
        return User.get_or_none(User.telegram_id == telegram_id)
    except Exception as e:
        print(f"[DB] Foydalanuvchini olishda xato: {e}")
        return None

async def get_new_gift(gift_id: int):
    from .models import Gift

    try:
        return Gift.get_or_none((Gift.id == gift_id) & (Gift.status == 'new'))
    except Exception as e:
        print(f"[DB] Giftni olishda xato: {e}")
        return None

async def deduct_stars(telegram_id: int, stars_amount: int):
    try:
        from .models import User
            
        user = User.get_or_none(User.telegram_id == telegram_id)
        if user:
            if user.stars >= stars_amount:
                user.stars -= stars_amount
                user.save()
                print(f"[DB] Foydalanuvchi {telegram_id} hisobidan {stars_amount} Stars ayirildi. Yangi balans: {user.stars}")
                return True
            else:
                print(f"[DB] Foydalanuvchi {telegram_id} hisobida Stars yetarli emas. Balans: {user.stars}, Kerakli: {stars_amount}")
                return False
        else:
            print(f"[DB] Foydalanuvchi topilmadi: {telegram_id}")
            return False
    except Exception as e:
        print(f"[DB] Stars ayirishda xatolik: {e}")
        return False

async def create_transaction(
    user_id: int, 
    status: str, 
    stars: int = None, 
    gift_id: str = None, 
    description: str = None,
):

    try:
        from .models import User, Transactions, Gift

        user = User.get_or_none(User.telegram_id == user_id)
        if not user:
            print(f"[DB_ERROR] Tranzaksiya yaratishda foydalanuvchi topilmadi: {user_id}")
            return False

        gift = None
        if gift_id:
            gift = Gift.get_or_none(Gift.id == gift_id)
            if not gift:
                print(f"[DB_WARNING] Tranzaksiya uchun gift topilmadi: {gift_id}")

        Transactions.create(
            user=user,
            gift=gift,
            timestamp=datetime.now(), # Hozirgi vaqt
            status=status,
            stars=stars,
        )
        print(f"[DB] Yangi tranzaksiya yozildi: User={user_id}, Status={status}, Stars={stars or 'N/A'}")
        return True
    except Exception as e:
        print(f"[DB_ERROR] Tranzaksiya yaratishda xato: {e}")
        return False

async def get_default_users():
    from .models import User
    return User.select().where(
        (User.is_premium == False) & (User.user_id > 0)
    )
