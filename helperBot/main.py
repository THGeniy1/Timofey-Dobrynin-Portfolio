import asyncio
import shutil

import datetime
import configparser

import aiogram.exceptions

from typing import Union

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

from DataBase import objectStorage, generalFunctions, usersFunctions
from handlers import mainHandler, startHandler, adminHandler, executorHandler, userHandler, ordersHandler, trashcan

from filters.middlewares import CheckChannelSubscribe, out_time_middleware, check_ban_middleware

config = configparser.ConfigParser()

config.read(r'D:\pythonProject\helperBot\config.ini')

main_path = config.get('DATA_BASE_PATH', 'orders_path')

API_TOKEN = config.get('TELEGRAM_CONFIGS', 'API')

channelID = config.get('TELEGRAM_CONFIGS', 'Channel_ID')

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

check_channel_subscribe = CheckChannelSubscribe(channel_id=[channelID], bot=bot)

dp = Dispatcher()

dp.message.middleware(out_time_middleware)
dp.callback_query.middleware(out_time_middleware)

dp.message.middleware(check_ban_middleware)
dp.callback_query.middleware(check_ban_middleware)

dp.message.middleware(check_channel_subscribe)
dp.callback_query.middleware(check_channel_subscribe)


async def start_clear():
    try:
        shutil.rmtree(path=main_path)
    except FileNotFoundError:
        pass


async def call_user(order_id: str, user_id: int):
    try:
        await bot.send_message(chat_id=user_id, text=f"⭐На заказ <b>№{order_id}</b> откликнулись⭐!\n\n"
                                                     "С помощью команды /orders можно посмотреть отклики")

    except aiogram.exceptions.TelegramForbiddenError:
        pass


async def notifications_active(users: list):
    for user in users:
        try:
            await bot.send_message(chat_id=user['id'], text="<b>Хей хей хей! Поступил новый заказ, бегом смотреть!😎\n"
                                                            "С помощью команды /show их можно увидеть</b>\n\n"
                                                            "С помощью команды /user можно отключить уведомления")

        except aiogram.exceptions.TelegramForbiddenError:
            pass


async def temporary_functions():
    clear_time = 16

    time_list = [8, clear_time, 18]

    while True:
        current_time = datetime.datetime.now()

        if current_time.hour in time_list:
            if current_time.hour == clear_time:
                await end_orders()
            else:
                all_users = await generalFunctions.getALLUsers()
                for user in all_users:
                    try:
                        await bot.send_message(chat_id=user['id'],
                                               text="Не забывай что здесь ты найдешь помощь по учебе!)😌")

                    except aiogram.exceptions.TelegramForbiddenError:
                        await generalFunctions.end_all_actions(data={"id": user['id']})

        sleeps = list(filter(lambda x: x > current_time.hour, time_list))

        if sleeps:
            time = min(sleeps)
            current_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
            time_off = time * 3600 - current_seconds

        else:
            next_run = current_time.replace(day=current_time.day + 1, hour=min(time_list), minute=0, second=0)
            time_off = (next_run - current_time).total_seconds()

        await asyncio.sleep(time_off)


async def prepare_dict(prep_lists: [list]):
    prep_dict = {}

    for index, prep_list in enumerate(prep_lists):
        if index == 0:
            category = "end"
        else:
            category = "notification"

        for val in prep_list:
            if val["user_id"] not in prep_dict:
                prep_dict[val["user_id"]] = {"end": [], "notification": []}

            prep_dict[val["user_id"]][category].append(val["id"])

    return prep_dict


async def end_orders():
    old_orders = await generalFunctions.get_old_orders()

    respond_orders = await generalFunctions.get_respond_orders()

    final_ids = await prepare_dict(prep_lists=[old_orders, respond_orders])

    for user in final_ids:
        user_text = ''
        if "end" in final_ids[user] and final_ids[user]["end"]:

            for end_order in final_ids[user]["end"]:
                await usersFunctions.end_order(data={"id": end_order})
            user_text += f"<b>Автоматически завершены заказы: {', '.join(map(str, final_ids[user]['end']))}</b>\n"

        if "notification" in final_ids[user] and final_ids[user]["notification"]:
            user_text += f"<b>Напоминаю, что на заказы: " \
                         f"{', '.join(', '.join(map(str, final_ids[user]['notification'])))} есть отклики</b>\n" \
                         f"Если задание уже выполнено, можно закрыть его с помощью команды: /user"

        try:
            await bot.send_message(chat_id=user, text=user_text)

        except aiogram.exceptions.TelegramForbiddenError:
            await generalFunctions.end_all_actions(data={"id": user})


async def downloader(message: Message, order_id: Union[str, int], insert_path: str):
    file = message.photo[-1]

    file_name = await get_file_name(message=message)

    file_path = f"{insert_path}/{file_name}"

    await bot.download(file=file, destination=file_path, timeout=60)

    await objectStorage.load_object(file_path=file_path, file_name=file_name, bucket_name=str(order_id))


async def get_file_name(message: Message):
    file = message.photo[-1]

    file_id = file.file_id

    file_info = await bot.get_file(file_id=file_id)

    file_path = file_info.file_path

    strip_path = file_path.split('/')

    return strip_path[-1]


async def main():
    dp.include_router(adminHandler.router)
    dp.include_router(mainHandler.router)

    dp.include_router(executorHandler.router)
    dp.include_router(ordersHandler.router)
    dp.include_router(userHandler.router)

    dp.include_router(startHandler.router)

    dp.include_router(trashcan.router)

    asyncio.create_task(temporary_functions())

    await start_clear()

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
