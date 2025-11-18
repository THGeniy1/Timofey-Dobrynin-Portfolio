import asyncio

import configparser

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.middlewares import out_time_middleware

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from DataBase import generalFunctions
from function import overallFunctions

config = configparser.ConfigParser()

config.read(r'D:\pythonProject\helperBot\config.ini')

adminID = config.get('TELEGRAM_CONFIGS', 'Admin_ID')

router = Router()


class Ban(StatesGroup):
    user = State()
    ban = State()


class SendMessage(StatesGroup):
    media = State()
    text = State()
    isLoad = State()


@router.message(Command(commands='block', prefix='/'))
async def ban_command(message: Message, state: FSMContext):
    if message.chat.id == int(adminID):
        await message.delete()
        data = await state.get_data()

        if "page" in data and data["page"]:
            await overallFunctions.deleteSendMessage(data=data["page"])

        if "media_message" in data and data["media_message"]:
            await overallFunctions.deleteSendMessage(data=data["media_message"])

        await state.clear()
        await state.set_state(Ban.user)

        send_message = await message.answer(text="Босс, введи ссылку или ID пользователя")
        await state.update_data(page=send_message)


@router.message(Ban.user)
async def reason_blocking(message: Message, state: FSMContext):
    await message.delete()
    await state.set_state(Ban.ban)

    send_message = await message.answer(text="Босс, введи причину бана пользователя")
    await state.update_data(user=message.text, page=send_message)


@router.message(Ban.ban)
async def ban_user(message: Message, state: FSMContext):
    await message.delete()

    data = await state.get_data()
    await state.clear()

    data["reason"] = message.text

    task = asyncio.create_task(generalFunctions.banUser(data=data))

    await task

    if task.done():
        await message.answer(text="Босс, он получил бан")
    else:
        await message.answer(text="Босс, он не зарегистрирован у нас")


@router.message(Command(commands='statistic', prefix='/'))
async def stats(message: Message, state: FSMContext):
    if message.chat.id == int(adminID):
        await message.delete()

        data = await state.get_data()
        await state.clear()

        if "page" in data:
            await overallFunctions.deleteSendMessage(data=data["page"])

        text = "<b>Статистика по боту:</b>\n" \
               "Текущий онлайн: <b>{}</b>\n" \
               "Количество пользователей: <b>{}</b>\n" \
               "Количество обычных заказов: <b>{}</b>\n" \
               "Количество премиум заказов: <b>0</b>\n"

        now_online = await out_time_middleware.get_online()
        count_users = await generalFunctions.getCountUsers()
        count_tasks = await generalFunctions.getCountOrders()

        send_message = await message.answer(text=text.format(now_online, count_users, count_tasks["count"]))

        await state.update_data(page=send_message)
