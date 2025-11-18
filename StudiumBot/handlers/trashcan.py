import aiogram.exceptions
from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def trashcan(message: Message):
    try:
        await message.delete()
    except aiogram.exceptions.TelegramBadRequest:
        pass
