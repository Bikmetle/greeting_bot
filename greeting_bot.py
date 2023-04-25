import logging
import os
import asyncio
from random import choice, randint, shuffle
from aiogram import Bot, types, filters
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from sql_model import MessageModel, SessionLocal
from config import TOKEN, OWNER, DEV, WEBHOOK_HOST, WEBHOOK_PATH, WEBAPP_HOST


WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_PORT = int(os.environ.get('PORT', '8443'))


logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


def captcha(member):
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=5)
    keyboard_items = [('steak', "🥩"), ('kiwi', "🥝"), ('milk', "🥛"), ('bacon', "🥓"),
                    ('coconut', "🥥"), ('donut', "🍩"), ('taco', "🌮"), ('pizza', "🍕"),
                    ('salad', "🥗"), ('banana', "🍌"), ('chestnut', "🌰"), ('lollipop', "🍭"),
                    ('avocado', "🥑"), ('chicken', "🍗"), ('sandwich', "🥪"), ('cucumber', "🥒")]
    shuffle(keyboard_items)
    index = randint(0,4)
    item = keyboard_items[:5].pop(index)
    right_item = ('right', item[1])
    keyboard_items[index] = right_item
    for i in range(5):
        keyboard.insert(
            types.InlineKeyboardButton(
                text=keyboard_items[i][1], 
                callback_data=f'{keyboard_items[i][0]} {member.id}'
            )
        )

    text = f"Привет, <a href='tg://user?id={member.id}'>{member.full_name}</a>!\nЕсли ты не БОТ и не СПАМЕР - нажми на кнопку {right_item[1]}"
    return text, keyboard


@dp.callback_query_handler(lambda query: query.data.startswith(('right')))
async def process_edit(query: types.CallbackQuery):
    _, member_id = query.data.split()
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    if user_id == int(member_id):
        text = f"<a href='tg://user?id={user_id}'>{query.from_user.full_name}</a> добро пожаловать в наш чат!\n" \
            "📌Просьба соблюдать простые правила в закрепленных сообщениях👆\n\n" \
            "ВНЖ. НОТАРИУС @Kaganatski\nБайер. Золото @istanbuldan_kyz\nЧартерные билеты. Туры @venuspower\n" \
            "Недвижимость @anara_realestate\nПо поводу рекламы писать @Kaganatski"
        await query.message.delete()
        permissions = types.ChatPermissions(can_send_messages=True, can_send_media_messages=True)
        await query.message.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions
        )
        message = await bot.send_message(chat_id, text=text, parse_mode="HTML")
        await asyncio.sleep(30)
        await message.delete()
    else:
        await query.answer(text='Это не твоя каптча', show_alert=True)


@dp.callback_query_handler(lambda query: query.data.startswith(('steak', 'kiwi', 'milk', 'bacon',
                                                                'coconut', 'donut', 'taco', 'pizza',
                                                                'salad', 'banana', 'chestnut', 'lollipop',
                                                                'avocado', 'chicken', 'sandwich', 'cucumber')))
async def process_edit(query: types.CallbackQuery):
    await query.answer(text='Неправильно!', show_alert=True)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    await bot.send_message(chat_id=DEV, text='Bot has been started')


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.send_message(chat_id=DEV, text='Bot has been stopped')
    logging.warning('Bye!')


@dp.message_handler(commands=['about'])
async def cmd_start_help(message: types.Message) -> None:
    await message.answer('Simple bot to greet new chat memebers with anti-ad function')


@dp.message_handler(commands=['chatid'])
async def send_welcome(message: types.Message):
    chat_id = message.chat.id
    await message.reply(f"Chat ID is\n{chat_id}")


@dp.message_handler(content_types=["new_chat_members"])
async def join_group(message: types.Message):
    """
    Restrict sending messages for new group members
    """
    members = message.new_chat_members
    try:
        await message.delete()
        for member in members:
            if member.is_bot:
                continue
            permissions = types.ChatPermissions(can_send_messages=False, can_send_media_messages=False)
            await message.bot.restrict_chat_member(
                message.chat.id,
                member.id,
                permissions
            )
            text, keyboard = captcha(member)
            await message.answer(text=text, reply_markup=keyboard, parse_mode="HTML")
    
    except Exception as e:
        await bot.send_message(chat_id=OWNER, text=f'join_group {e}')
        await bot.send_message(chat_id=DEV, text=f'join_group {e}')
        

chat_filter = filters.ChatTypeFilter(types.ChatType.SUPERGROUP)
@dp.message_handler(chat_filter)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    text = message.text
    date = message.date

    db = SessionLocal()
    db_message = MessageModel(
        user_id=user_id,
        full_name=full_name,
        username=username,
        text=text,
        date=date
    )
    db.add(db_message)
    db.commit()
    db.close()


@dp.message_handler(content_types=[types.ContentType.PHOTO])
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    file_id = message.photo[-1]['file_unique_id']
    date = message.date

    db = SessionLocal()
    db_message = MessageModel(
        user_id=user_id,
        full_name=full_name,
        username=username,
        file_id=file_id,
        date=date
    )
    db.add(db_message)
    db.commit()
    db.close()

# if __name__ == '__main__':
    # dp.register_update_handler(ChatMemberUpdated, ChatMembersJoin())
#     executor.start_webhook(
#         dispatcher=dp,
#         webhook_path=WEBHOOK_PATH,
#         on_startup=on_startup,
#         on_shutdown=on_shutdown,
#         skip_updates=True,
#         host=WEBAPP_HOST,
#         port=WEBAPP_PORT,
#     )


if __name__ == '__main__':
    executor.start_polling(dp)