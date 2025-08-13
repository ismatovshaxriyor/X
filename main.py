from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters, PreCheckoutQueryHandler
from telegram import Update
import logging
import asyncio
import html


from config import API_TOKEN, ADMIN_ID
from database.db import init_db
from handlers.user import (
    start_command,
    help_command, 
    premium_command, 
    set_gift_prefs_command, 
    send_stars_invoice, 
    start_process_command,
    stop_process_command,
    info_command,
    refund_payment_command,
    channels_command
)
from handlers.manager import manager_callback
from handlers.admin import send_logs
from handlers.payment_callback import pre_checkout_callback, successful_payment
from handlers.chech_agree_dec import agreement_callback_handler
from handlers.add_channels import add_channel_conv_handler
from handlers.get_channel import get_channel_callback
from handlers.delete_channels import delete_channel_callback
from handlers.back_channel import back_channels_callback
from handlers.sent_to_callback import set_sentTo_callback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

global_app_instance: Application = None
def set_global_app_instance(app_instance: Application):
    global global_app_instance
    global_app_instance = app_instance


def get_global_app_instance() -> Application:
    """Global Application obyektini qaytaradi."""
    if global_app_instance is None:
        raise RuntimeError("Application obyekti hali o'rnatilmagan.")
    return global_app_instance

async def error_handler(update, context):
    import traceback
    traceback.print_exc()
    logger.error("Botda xatolik yuz berdi: %s", context.error)
    
    # Xato ma'lumotini saqlash
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    
    # Xato xabari uchun HTML matnini shakllantirish
    message = (
        "<b>Botda xatolik yuz berdi!</b>\n\n"
        f"<b>Update:</b> <pre>{html.escape(str(update_str))}</pre>\n\n"
        f"<b>Xatolik:</b> <pre>{html.escape(str(context.error))}</pre>\n\n"
        f"<b>Traceback:</b> <pre>{html.escape(tb_string)}</pre>"
    )
    
    # Adminka xabarni yuborish
    if ADMIN_ID:
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=message, 
            parse_mode='HTML'
        )

async def start_all():
    from services.telethon import main_userbot
    
    init_db()
    application = Application.builder().token(API_TOKEN).build()
    set_global_app_instance(application)
    
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('premium', premium_command))
    application.add_handler(CommandHandler('set_gift_prefs', set_gift_prefs_command))
    application.add_handler(CommandHandler('donate', send_stars_invoice))
    application.add_handler(CommandHandler("start_process", start_process_command))
    application.add_handler(CommandHandler("stop_process", stop_process_command))
    application.add_handler(CommandHandler('info', info_command))
    application.add_handler(CommandHandler("refund", refund_payment_command))
    application.add_handler(CommandHandler('channels', channels_command))

    application.add_handler(add_channel_conv_handler)

    application.add_handler(CallbackQueryHandler(manager_callback, pattern=r"^(approve|reject)_\d+$"))
    application.add_handler(CallbackQueryHandler(agreement_callback_handler, pattern=r"^(agree|disagree)_\d+$"))
    application.add_handler(CallbackQueryHandler(get_channel_callback, pattern=r"^chnl_"))
    application.add_handler(CallbackQueryHandler(delete_channel_callback, pattern=r"^delete_"))
    application.add_handler(CallbackQueryHandler(back_channels_callback, pattern=r"back_channels"))
    application.add_handler(CallbackQueryHandler(set_sentTo_callback, pattern=r"^sendTo_"))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("get_logs", send_logs))
    
    async with application:
        userbot_task = asyncio.create_task(main_userbot(application))
        
        await application.start()
        await application.updater.start_polling()
        
        await userbot_task
        
        await application.updater.stop()
        await application.stop()
    
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()


if __name__ == "__main__":
    asyncio.run(start_all())