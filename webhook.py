import logging
import os
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from config import TOKEN, OWNER, DEV

API_TOKEN = TOKEN
WEBHOOK_HOST = 'https://testwebhookheroku.herokuapp.com'
WEBHOOK_PATH = '/'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.environ.get('PORT', '8443'))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    await bot.send_message(chat_id=DEV, text='Bot has been started')

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.send_message(chat_id=DEV, text='Bot has been stopped')
    logging.warning('Bye!')

@dp.message_handler(commands=['start', 'help'])
async def cmd_start_help(message: types.Message) -> None:
    await message.answer('Hello, welcome to our webhook bot!')

@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(chat_id=msg.from_user.id, text=f"<b>{msg.text}</b>", parse_mode="HTML")

if __name__ == '__main__':
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )