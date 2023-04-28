import logging
import os
import asyncio
from random import randint, shuffle
from aiogram import Bot, types, filters
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from sql_model import MessageModel, Session
from config import TOKEN, OWNER, DEV, WEBHOOK_HOST, WEBHOOK_PATH, WEBAPP_HOST
from sqlalchemy import func


WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_PORT = int(os.environ.get('PORT', '8443'))


logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


def ad_id_and_text(text):
    ad_id = int(text[text.index('[') + 1:text.index('].\n')])
    text = text[text.index(']\n') + 2:]
    return ad_id, text


def get_user_link(message: types.Message):
    """
    This function gets user as a link.
    """
    id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    if message.from_user.username is not None:
        user_link = f"[{id}]\nСообщение от <a href='tg://user?id={id}'>{full_name}</a> @{username}\n"
    else:
        user_link = f"[{id}]\nСообщение от <a href='tg://user?id={id}'>{full_name}</a>\n"
    return user_link


def get_user_link_2(user_id, full_name, username):
    """
    This function gets user as a link.
    """
    if username is not None:
        user_link = f"[{user_id}]\nСообщение от <a href='tg://user?id={id}'>{full_name}</a> @{username}\n"
    else:
        user_link = f"[{user_id}]\nСообщение от <a href='tg://user?id={id}'>{full_name}</a>\n"
    return user_link


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
async def process_right_query(query: types.CallbackQuery):
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
        message = await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        await asyncio.sleep(30)
        await message.delete()
    else:
        await query.answer(text='Это не твоя каптча', show_alert=True)


@dp.callback_query_handler(lambda query: query.data.startswith(('steak', 'kiwi', 'milk', 'bacon',
                                                                'coconut', 'donut', 'taco', 'pizza',
                                                                'salad', 'banana', 'chestnut', 'lollipop',
                                                                'avocado', 'chicken', 'sandwich', 'cucumber')))
async def process_wrong_query(query: types.CallbackQuery):
    await query.answer(text='Неправильно!', show_alert=True)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    await bot.send_message(chat_id=OWNER, text='Bot has been started')
    await bot.send_message(chat_id=DEV, text='Bot has been started')


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.send_message(chat_id=OWNER, text='Bot has been stopped')
    await bot.send_message(chat_id=DEV, text='Bot has been stopped')
    logging.warning('Bye!')


@dp.message_handler(commands=['about'])
async def about_msg(message: types.Message) -> None:
    await message.answer('Simple bot to greet new chat memebers with anti-ad function')


@dp.message_handler(commands=['chatid'])
async def chat_id_msg(message: types.Message):
    chat_id = message.chat.id
    await message.reply(f"Chat ID is\n{chat_id}")


@dp.message_handler(commands=['status'])
async def status_msg(message: types.Message):
    user_id = message.from_user.id
    if message.reply_to_message and user_id in [OWNER, DEV]:
        session = Session()
        try:
            ad_id, _ = ad_id_and_text(message.reply_to_message.text)
            obj = session.query(MessageModel).filter_by(id=ad_id).first()
            user_link = get_user_link_2(obj.user_id, obj.full_name, obj.username)
            text=f'[{obj.id}].\n{user_link}{obj.text}\n{obj.count} ads left'
            await bot.send_message(chat_id=OWNER, text=text, parse_mode="HTML")
            await bot.send_message(chat_id=DEV, text=text, parse_mode="HTML")
        except:
            ad_id, _ = ad_id_and_text(message.reply_to_message.caption)
            obj = session.query(MessageModel).filter_by(id=ad_id).first()
            user_link = get_user_link_2(obj.user_id, obj.full_name, obj.username)
            photo=message.reply_to_message.photo[-1].file_id
            caption=f'[{obj.id}].\n{user_link}{obj.text if obj.text else ""}\n{obj.count} ads left'
            await bot.send_photo(chat_id=OWNER, photo=photo, caption=caption, parse_mode="HTML")
            await bot.send_photo(chat_id=DEV, photo=photo, caption=caption, parse_mode="HTML")
        await message.delete()
        await message.reply_to_message.delete()


@dp.message_handler(commands=['spam'])
async def spam_msg(message: types.Message):
    user_id = message.from_user.id
    if message.reply_to_message and user_id in [OWNER, DEV]:
        try:
            ad_id, _ = ad_id_and_text(message.reply_to_message.text)
        except:
            ad_id, _ = ad_id_and_text(message.reply_to_message.caption)

        session = Session()
        session.query(MessageModel).filter_by(id=ad_id).update({'count': -1})
        session.commit()
        await message.delete()


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
            greeting = await message.answer(text=text, reply_markup=keyboard, parse_mode="HTML")
            await asyncio.sleep(30)
            await greeting.delete()

    except Exception as e:
        await bot.send_message(chat_id=OWNER, text=f'join_group {e}')
        await bot.send_message(chat_id=DEV, text=f'join_group {e}')
        

chat_filter = filters.ChatTypeFilter(types.ChatType.SUPERGROUP)
@dp.message_handler(chat_filter)
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    message_id = message.message_id
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    text = message.text
    date = message.date
    user_link = get_user_link(message)

    session = Session()
    obj = session.query(MessageModel).filter_by(text=text).first()
    try:
        if obj.count > 0:
            session.query(MessageModel).filter_by(id=obj.id).update({'count': obj.count-1})
            session.commit()
        elif obj.count < 0:
            session.query(MessageModel).filter_by(id=obj.id).update({'count': obj.count-1})
            session.commit()
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        else:
            await bot.send_message(chat_id=OWNER, text=f"[{obj.id}].\n{user_link}{text}\n{obj.count} ads left", parse_mode="HTML")
            await bot.send_message(chat_id=DEV, text=f"[{obj.id}].\n{user_link}{text}\n{obj.count} ads left", parse_mode="HTML")
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        db_message = MessageModel(
            id = message_id,
            user_id=user_id,
            full_name=full_name,
            username=username,
            text=text,
            date=date
        )
        session.add(db_message)
        ids_to_delete = [row.id for row in session.query(MessageModel).filter_by(user_id=user_id).all()]
        while len(ids_to_delete) > 10:
            id = ids_to_delete.pop(0)
            obj = session.query(MessageModel).filter_by(id=id)
            if obj.first().count:
                continue
            else:
                obj.delete()
        session.commit()


@dp.message_handler(chat_filter, content_types=[types.ContentType.PHOTO])
async def handle_photo(message: types.Message):
    chat_id = message.chat.id
    message_id = message.message_id
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    file_id = message.photo[-1]['file_unique_id']
    caption = message.caption
    date = message.date
    user_link = get_user_link(message)

    session = Session()
    obj = session.query(MessageModel).filter_by(file_id=file_id).first()
    try:
        if obj.count:
            session.query(MessageModel).filter_by(id=obj.id).update({'count': obj.count-1})
            session.commit()
        else:
            await bot.send_photo(chat_id=OWNER, photo=message.photo[-1].file_id, caption=f'[{obj.id}].\n{user_link}{caption if caption else ""}\n{obj.count} ads left', parse_mode="HTML")
            await bot.send_photo(chat_id=DEV, photo=message.photo[-1].file_id, caption=f'[{obj.id}].\n{user_link}{caption if caption else ""}\n{obj.count} ads left', parse_mode="HTML")
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        db_message = MessageModel(
            id = message_id,
            user_id=user_id,
            full_name=full_name,
            username=username,
            text=caption,
            file_id=file_id,
            date=date
        )
        session.add(db_message)
        ids_to_delete = [row.id for row in session.query(MessageModel).filter_by(user_id=user_id).all()]
        while len(ids_to_delete) > 5:
            id = ids_to_delete.pop(0)
            obj = session.query(MessageModel).filter_by(id=id)
            if obj.first().count:
                continue
            else:
                obj.delete()
        session.commit()


@dp.message_handler()
async def manage_count(message: types.Message):
    user_id = message.from_user.id
    if message.reply_to_message and user_id in [OWNER, DEV]:
        try:
            new_count = int(message.text)
            session = Session()
            try:
                ad_id, _ = ad_id_and_text(message.reply_to_message.text)
                obj = session.query(MessageModel).filter_by(id=ad_id).first()
                user_link = get_user_link_2(obj.user_id, obj.full_name, obj.username)
                text=f'[{obj.id}].\n{user_link}{obj.text}\n{new_count} ads left'
                await bot.send_message(chat_id=OWNER, text=text, parse_mode="HTML")
                await bot.send_message(chat_id=DEV, text=text, parse_mode="HTML")
            except:
                ad_id, _ = ad_id_and_text(message.reply_to_message.caption)
                obj = session.query(MessageModel).filter_by(id=ad_id).first()
                user_link = get_user_link_2(obj.user_id, obj.full_name, obj.username)
                photo = message.reply_to_message.photo[-1].file_id
                caption = f'[{obj.id}].\n{user_link}{obj.text if obj.text else ""}\n{new_count} ads left'
                await bot.send_photo(chat_id=OWNER, photo=photo, caption=caption, parse_mode="HTML")
                await bot.send_photo(chat_id=DEV, photo=photo, caption=caption, parse_mode="HTML")
            session.query(MessageModel).filter_by(id=ad_id).update({'count': new_count})
            session.commit()
            await message.delete()
        except:
            await message.answer(text='reply to ad msg please')


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