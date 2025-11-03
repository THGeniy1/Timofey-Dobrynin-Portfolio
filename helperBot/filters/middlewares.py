import asyncio
import aiogram.exceptions

from typing import Any, Callable, Dict, Awaitable, Union

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, TelegramObject, ReplyKeyboardRemove
from markups import distrubMarkups

from Other import Texts

from DataBase import generalFunctions


class AlbumMiddleware(BaseMiddleware):
    def __init__(self):
        self.album_data: dict = {}
        self.time_data: dict = {}

        self.latency = 1
        self.media_number = 10
        self.free_MegaBytes = 10

        super().__init__()

    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: Message, data: Dict[str, Any]) -> Any:

        async def sendError(states_data: dict, is_len_error: bool):
            if is_len_error:
                send_message = await event.answer(text="❌Превышен лимит фотографий в 10 фотографий")
            else:
                send_message = await event.answer(text="❌Превышен лимит веса фотографий в 10 МБ")

            if isinstance(states_data["page"], list):
                states_data["page"].append(send_message)
            else:
                states_data["page"] = [states_data["page"], send_message]

            await data["state"].update_data(page=states_data["page"])

        async def outTask():
            await asyncio.sleep(self.latency)

            add_data = self.album_data.pop(event.chat.id)['event']
            states_data = await data["state"].get_data()

            if active_state not in states_data:
                states_data[active_state] = []

            if len(states_data[active_state]) == self.media_number:
                await sendError(states_data=states_data, is_len_error=True)
                return
            else:

                add_count = self.media_number - len(states_data[active_state])

                free_space = self.free_MegaBytes * 1024 * 1024

                for value in states_data[active_state]:
                    free_space -= value.photo[0].file_size

                for add_value in add_data[0:add_count]:
                    size = add_value.photo[-3].file_size

                    space = free_space - size

                    if space >= 0:
                        free_space -= size
                        states_data[active_state].append(add_value)
                    else:
                        await sendError(states_data=states_data, is_len_error=False)
                        break

                await data["state"].update_data(photos=states_data[active_state])

                return await handler(event, data)

        if data["raw_state"]:
            active_state = (data['raw_state']).split(':')[1]

            if active_state != "photos":
                if event.content_type == "text":
                    return await handler(event, data)
                else:
                    await event.delete()
                    return

            await event.delete()

            try:
                if len(self.album_data[event.chat.id]['event']) < self.media_number:
                    self.album_data[event.chat.id]['event'].append(event)
                    self.album_data[event.chat.id]['task'].cancel()
                    self.album_data[event.chat.id]['task'] = asyncio.create_task(outTask())
                    await asyncio.sleep(0.5)

            except KeyError:
                self.album_data[event.chat.id] = {}
                self.album_data[event.chat.id]['event'] = [event]
                self.album_data[event.chat.id]['task'] = asyncio.create_task(outTask())
                await asyncio.sleep(0.5)
        else:
            return await handler(event, data)


class OutTimeMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_dict = {}

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:

        async def deleter(message: Message):
            try:
                await message.delete()

            except aiogram.exceptions.TelegramBadRequest:
                pass

        async def deleteSendMessage(messages_data: Union[list, Message]):
            if isinstance(messages_data, list):
                for m in messages_data:
                    if isinstance(m, list):
                        for subMessage in m:
                            await deleter(subMessage)
                    else:
                        await deleter(m)
            else:
                await deleter(messages_data)

        async def endCommunicate(message: Message, state: FSMContext):
            await asyncio.sleep(900)

            state_data = await state.get_data()

            await deleter(message=message)
            await state.clear()

            if "page" in state_data and state_data["page"]:
                await deleteSendMessage(messages_data=state_data["page"])

            if "media_message" in state_data and state_data["media_message"]:
                await deleteSendMessage(messages_data=state_data["media_message"])

            await message.answer(text="💤Произведена очистка💤", reply_markup=ReplyKeyboardRemove())
            self.user_dict.pop(message.chat.id, None)

        if isinstance(event, Message):
            user_id = event.chat.id
            end_task = asyncio.create_task(endCommunicate(message=event, state=data["state"]))
        else:
            user_id = event.message.chat.id
            end_task = asyncio.create_task(endCommunicate(message=event.message, state=data["state"]))

        if user_id in self.user_dict:
            self.user_dict[user_id].cancel()

        self.user_dict[user_id] = end_task

        return await handler(event, data)

    async def get_online(self):
        return len(self.user_dict)


class CheckChannelSubscribe(BaseMiddleware):
    def __init__(self, channel_id, bot):
        self.chanel_id = channel_id
        self.bot = bot

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:

        if isinstance(event, Message):
            user_id = event.chat.id
        else:
            user_id = event.message.chat.id

        for channel in self.chanel_id:
            user_status = await self.bot.get_chat_member(chat_id=channel, user_id=user_id)

            if user_status.status != "left":
                return await handler(event, data)
            else:
                markup = await distrubMarkups.check_subscribe_markup()

                if isinstance(event, Message):
                    await event.delete()
                    await event.answer(text=Texts.subscribe_text, reply_markup=markup)
                else:
                    await event.message.delete()
                    await event.message.answer(text=Texts.subscribe_text, reply_markup=markup)

                return False


class CheckBanMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:

        if isinstance(event, Message):
            message = event
        else:
            message = event.message

        user_id = message.chat.id
        if await generalFunctions.checkInBlockedList(user_id):
            await event.answer(text="Ты забанен, не пиши мне больше😭!")
            await data["state"].clear()
            return False
        else:
            return await handler(event, data)


out_time_middleware = OutTimeMiddleware()
check_ban_middleware = CheckBanMiddleware()
album_middleware = AlbumMiddleware()
