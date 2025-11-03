from typing import Union

import aiogram.exceptions
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from Other import Texts

from DataBase import generalFunctions


class IsModuleCommands(Filter):
    def __init__(self, commands: Union[str, list]):
        self.commands = commands

    async def __call__(self, message: Message):
        if message.content_type == "text":
            if message.text.startswith('/'):
                if isinstance(self.commands, str):
                    return message.text == self.commands
                else:
                    return message.text in self.commands
            else:
                return True
        else:
            return True


class CallBackFilter(Filter):
    def __init__(self, commands: Union[str, list]):
        self.commands = commands

    async def __call__(self, callback: CallbackQuery):
        if isinstance(self.commands, str):
            return callback.data == self.commands
        else:
            return callback.data in self.commands


class PriceFilter(Filter):
    async def __call__(self, message: Message, state: FSMContext):
        if message.content_type == "text":
            try:
                price = float(message.text)
                data = await state.get_data()
                if 'order_data' not in data:
                    if price >= Texts.types_list[data["work_type"]]:
                        return True
                    else:
                        return False
                else:
                    return True

            except ValueError:
                return False
        else:
            return False


class InRangeFilter(Filter):
    def __init__(self, start: Union[int], end: Union[int]):
        self.start_int = start
        self.end_int = end

    async def __call__(self, message: Message):
        if message.content_type == "text":
            try:
                if self.start_int <= float(message.text) <= self.end_int:
                    return True
                else:
                    return False

            except ValueError:
                return False
        else:
            return False


class CheckRegFilter(Filter):
    async def __call__(self, message: Message):

        is_reg = await generalFunctions.checkInUserList(data=message.chat.id)

        if is_reg:
            return True
        else:
            return False


class IsHaveDataFilter(Filter):
    async def __call__(self, callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()

        if data:
            return True
        else:
            try:
                await callback.message.delete()
            except aiogram.exceptions.TelegramBadRequest and AttributeError:
                pass

            return False
