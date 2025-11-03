import asyncio

from Other import Texts

from aiogram import Router

from aiogram.filters import Command

from aiogram.fsm.state import State, StatesGroup

from aiogram.types import Message, CallbackQuery

from aiogram.fsm.context import FSMContext

from filters.filters import IsModuleCommands, CallBackFilter

from function import overallFunctions

from DataBase import generalFunctions

router = Router()

router.message.filter(IsModuleCommands(commands=["/start", "/help", "/instruction"]))


class UserStates(StatesGroup):
    city = State()
    university = State()
    correcting = State()


@router.callback_query(CallBackFilter(commands="/start"))
async def start_callback(callback: CallbackQuery, state: FSMContext):
    asyncio.create_task(start_bot(message=callback.message, state=state))


@router.message(Command(commands=['start'], prefix='/'))
async def start_command(message: Message, state: FSMContext):
    await overallFunctions.clearOld(state=state)

    asyncio.create_task(start_bot(message=message, state=state))


async def start_bot(message: Message, state: FSMContext):
    await message.delete()

    if not await generalFunctions.checkInUserList(data=message.chat.id):
        await generalFunctions.addNewUser(data={"id": message.chat.id,
                                                "user_name": message.chat.first_name,
                                                "user_link": f"@{message.chat.username}"})

    send_message = await message.answer(text=Texts.command_message)

    await state.update_data(page=send_message)


@router.message(Command(commands=['help'], prefix='/'))
async def process_help_command(message: Message, state: FSMContext):
    await message.delete()

    send_message = await message.answer(text=Texts.guide_message)

    await state.update_data(page=send_message)


@router.message(Command(commands=['instruction'], prefix='/'))
async def process_help_command(message: Message):
    await message.delete()

    await message.answer(text=Texts.instruction_message)
