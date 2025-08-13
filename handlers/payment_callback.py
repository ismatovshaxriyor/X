from peewee import IntegrityError
from database.models import User, Payment


async def pre_checkout_callback(update, context):
    query = update.pre_checkout_query

    if query.invoice_payload.startswith("stars_purchase_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="To'lov qilishda xatolik!")


async def successful_payment(update, context):
    payment = update.message.successful_payment
    payment_id = payment.telegram_payment_charge_id
    amount = payment.total_amount
    user_id = update.effective_user.id

    try:
        user = User.get(telegram_id=user_id)
        user.stars += amount
        user.save()

        Payment.create(
            user=user,
            telegram_payment_charge_id=payment_id,
            invoice_payload=payment.invoice_payload,
            status='SUCCESSS',
            currency=payment.currency,
            amount=amount
        )
        print(f"To'lov ma'lumotlari muvaffaqiyatli saqlandi: {user_id}")
    except IntegrityError as e:
        print(f"Xatolik: To'lov ma'lumotlari allaqachon mavjud. {e}")
    except Exception as e:
        Payment.create(
            user=user,
            telegram_payment_charge_id=payment_id,
            invoice_payload=payment.invoice_payload,
            status='FAILED',
            currency=payment.currency,
            amount=amount
        )
        print(f"Ma'lumotlarni saqlashda kutilmagan xatolik yuz berdi: {e}")