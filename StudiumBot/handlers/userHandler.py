import asyncio

from aiogram import Router

from aiogram.filters import Command

from aiogram.types import Message, CallbackQuery

from aiogram.fsm.context import FSMContext

from filters.filters import CheckRegFilter, CallBackFilter, IsHaveDataFilter, IsModuleCommands

from DataBase import usersFunctions, executorFunctions, generalFunctions

from function import overallFunctions

from markups import distrubMarkups

router = Router()

router.message.filter(CheckRegFilter(), IsModuleCommands(commands=["/user"]))


@router.message(Command(commands='user', prefix='/'))
async def user_status_command(message: Message, state: FSMContext):
    await message.delete()

    await overallFunctions.clearOld(state=state)
    await overallFunctions.update_user_info(message=message)

    user_data = await generalFunctions.getUser(user_id=message.chat.id, user_name=None, cursor=None)

    await state.update_data(user_data=user_data)

    message_text = await overallFunctions.showUserData(data=user_data, from_call="user")
    markup = await distrubMarkups.create_user_markup()

    send_message = await message.answer(text=message_text, reply_markup=markup)
    await state.update_data(page=send_message)


@router.callback_query(CallBackFilter(commands="/show_orders_back"), IsHaveDataFilter())
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    asyncio.create_task(user_status_command(callback.message, state))


@router.callback_query(CallBackFilter(commands="/malling"), IsHaveDataFilter())
async def change_malling(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_data = data["user_data"]

    if user_data["enabled"] == 'Y':
        user_data["enabled"] = 'N'
    else:
        user_data["enabled"] = 'Y'

    task = asyncio.create_task(usersFunctions.changeStateMalling(data=user_data))

    await task

    if task.done():
        asyncio.create_task(user_status_command(message=callback.message, state=state))
    else:
        await callback.message.answer(text="❌Что-то пошло не так при работе с базой данных, попробуй позже")


@router.callback_query(lambda query: query.data.split(",")[0] in ["/rating"], IsHaveDataFilter())
async def rating_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    data = await state.get_data()

    if "user_data" not in data:
        split_data = callback.data.split(',')
        user_id = int(split_data[1])

        user_data = await generalFunctions.getUser(user_id=user_id, user_name=None, cursor=None)

        data["user_data"] = user_data

        await state.set_data(data=data)

    await state.update_data(page_rating=0, is_forward=True, is_first=True)

    asyncio.create_task(show_rating(message=callback.message, state=state))


async def send_rating_title_message(message: Message, data: dict):
    messages_list = []

    if "rating_page" not in data or not data["rating_page"]:
        if "page" in data:
            await overallFunctions.deleteSendMessage(data["page"])

        if "from_call" in data:
            index = 1
        else:
            index = 0

        markup = await distrubMarkups.create_back_rate_markup(from_call=index)

        user_data = data["user_data"]

        title_text = f"<b>Показаны отзывы пользователя:</b>\n" \
                     f"Имя пользователя: <b>{user_data['user_name']}</b>\n" \
                     f"Ссылка на пользователя: <b>{user_data['user_link']}</b>\n" \
                     f"Рейтинг: <b>{user_data['rate_score']}</b>\n" \
                     f"Количество оценок: <b>{user_data['rate_count']}</b>"

        title_message = await message.answer(text=title_text, reply_markup=markup)

        messages_list.append(title_message)
    else:
        await overallFunctions.deleteSendMessage(data=data["rating_page"])
        messages_list.append(data["page"][0])

    data["page"] = messages_list

    return data


async def send_rating_messages(message: Message, data: dict, result: dict):
    rates_messages = []

    for rate in result["rates"]:
        order_text = f"Имя пользователя: <b>{rate['rated_user_name']}</b>\n" \
                     f"Ссылка на пользователя: <b>{rate['rated_user_link']}</b>\n" \
                     f"Оценка: <b>{rate['score']}</b>\n" \
                     f"Отзыв: <b>{rate['review']}</b>"

        message_1 = await message.answer(text=order_text)

        rates_messages.append(message_1)

    markup = await distrubMarkups.create_page_mover_markup(index=2, is_forward=data["is_forward"],
                                                           is_more_take=result["is_more_take"],
                                                           is_first=data["is_first"])
    if markup:
        message_2 = await message.answer(text="Показать еще отзывы?", reply_markup=markup)
        rates_messages.append(message_2)

    data["page_rating"] = result["page_rating"]

    data["rating_page"] = rates_messages

    data["page"].append(rates_messages)

    return data


async def show_rating(message: Message, state: FSMContext):
    data = await state.get_data()

    task = asyncio.create_task(usersFunctions.get_user_rate(data=data))

    await task

    if task.done():
        data = await send_rating_title_message(message=message, data=data)

        result = task.result()

        if result["rates"]:

            data = await send_rating_messages(message=message, data=data, result=result)

        else:
            absence_message = await message.answer(text="Оценок не обнаружено...😓")
            await state.update_data(page=absence_message)

        await state.set_data(data)

    else:
        await message.answer(text="❌Что-то пошло не так при работе с базой данных, попробуй позже")


@router.callback_query(lambda query: query.data.split(",")[0] in ["/show_rates"], IsHaveDataFilter())
async def rates_mover(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    is_first = False
    is_forward = bool(int(callback.data.split(',')[1]))

    if not is_forward and data["page_rating"] <= 1:
        is_forward = True,
        data["page_rating"] = 0
        is_first = True

    await state.update_data(user_id=callback.message.chat.id,
                            page_rating=data["page_rating"],
                            is_forward=is_forward,
                            is_first=is_first)

    asyncio.create_task(show_rating(callback.message, state))


@router.callback_query(CallBackFilter(commands=["/rate_back"]), IsHaveDataFilter())
async def rate_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    data.pop("page_rating")
    if "rating_page" in data:
        data.pop("rating_page")

    await state.set_data(data=data)

    asyncio.create_task(user_status_command(message=callback.message, state=state))


@router.callback_query(CallBackFilter(commands=["/responses"]), IsHaveDataFilter())
async def user_responds(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    await state.update_data(page_responds=0, is_forward=True, is_first=True)

    asyncio.create_task(show_responds(message=callback.message, state=state))


async def send_respond_title_message(message: Message, data: dict):
    messages_list = []

    if "responds_page" not in data or not data["responds_page"]:
        if "page" in data:
            await overallFunctions.deleteSendMessage(data["page"])

        counts = await executorFunctions.get_responds_counts(data={"id": data["user_data"]["id"]})

        markup = await distrubMarkups.create_back_responds_markup()

        title_text = f"<b>Показаны отклики на заказы</b>\n" \
                     f"Всего откликов: <b>{counts['all_count']}</b>\n" \
                     f"Активных откликов: <b>{counts['active_count']}</b>"

        title_message = await message.answer(text=title_text, reply_markup=markup)

        messages_list.append(title_message)
    else:
        await overallFunctions.deleteSendMessage(data=data["responds_page"])
        messages_list.append(data["page"][0])

    data["page"] = messages_list

    return data


async def send_respond_messages(message: Message, data: dict, result: dict):
    responds_messages = []

    for index, order in enumerate(result["responds"]):
        order_text = await overallFunctions.create_respond_list(respond_data=order, is_full=False)

        markup = await distrubMarkups.create_show_respond_markup(index=index)

        message_1 = await message.answer(text=order_text, reply_markup=markup)

        responds_messages.append(message_1)

    markup = await distrubMarkups.create_page_mover_markup(index=3,
                                                           is_forward=data["is_forward"],
                                                           is_more_take=result["is_more_take"],
                                                           is_first=data["is_first"])
    if markup:
        message_2 = await message.answer(text="Показать еще отклики?", reply_markup=markup)
        responds_messages.append(message_2)

    data["page_responds"] = result["page_responds"]

    data["responds_data"] = result["responds"]

    data["responds_page"] = responds_messages

    data["page"].append(responds_messages)

    return data


async def show_responds(message: Message, state: FSMContext):
    data = await state.get_data()

    task = asyncio.create_task(executorFunctions.get_user_responds(data=data))

    await task

    if task.done():
        data = await send_respond_title_message(message=message, data=data)

        result = task.result()

        if result["responds"]:

            data = await send_respond_messages(message=message, data=data, result=result)

        else:
            absence_message = await message.answer(text="Отклики не обнаружены, откликнуться на заказы можно "
                                                        "с помощью команды /show🤠")
            data["page"].append(absence_message)

        await state.set_data(data)

    else:
        await message.answer(text="❌Что-то пошло не так при работе с базой данных, попробуй позже")


@router.callback_query(lambda query: query.data.split(",")[0] in ["/show_responds"], IsHaveDataFilter())
async def responds_mover(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    is_first = False
    is_forward = bool(int(callback.data.split(',')[1]))

    if not is_forward and data["page_responds"] <= 1:
        is_forward = True,
        data["page_responds"] = 0
        is_first = True

    await state.update_data(page_responds=data["page_responds"], is_forward=is_forward, is_first=is_first)

    asyncio.create_task(show_responds(callback.message, state))


@router.callback_query(CallBackFilter(commands=["/responds_back"]), IsHaveDataFilter())
async def responds_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if "responds_page" in data:
        data.pop("responds_page")

    if "responds_data" in data:
        data.pop("responds_data")

    data.pop("page_responds")
    data.pop("is_forward")
    data.pop("is_first")

    await state.set_data(data=data)

    asyncio.create_task(user_status_command(message=callback.message, state=state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/show_respond"], IsHaveDataFilter())
async def show_respond(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await overallFunctions.deleteSendMessage(data=data["page"])

    split_data = callback.data.split(',')
    index = int(split_data[1])

    respond_data = data["responds_data"][index]

    respond_text = await overallFunctions.create_respond_list(respond_data=respond_data, is_full=True)

    message_1 = await callback.message.answer(text=respond_text)
    message_list = [message_1]

    media = await overallFunctions.createMediaMessages(order_data=respond_data)

    if media:
        message_2 = await callback.message.answer_media_group(media=media)
        message_list.append(message_2)

    markup = await distrubMarkups.create_respond_actions_markup(index=index)

    message_3 = await callback.message.answer(text="Что хочешь сделать?", reply_markup=markup)
    message_list.append(message_3)

    await state.update_data(show_respond=message_list)


@router.callback_query(CallBackFilter(commands=["/respond_back"]), IsHaveDataFilter())
async def respond_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await overallFunctions.deleteSendMessage(data=data["show_respond"])

    data.pop("show_respond")
    data.pop("responds_page")

    data["page_responds"] -= 1

    if data["page_responds"] <= 0:
        data["is_first"] = True

    await state.set_data(data=data)

    asyncio.create_task(show_responds(message=callback.message, state=state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/respond_end"], IsHaveDataFilter())
async def respond_end(callback: CallbackQuery):
    split_data = callback.data.split(',')
    index = split_data[1]

    markup = await distrubMarkups.create_end_respond_markup(index=index)

    await callback.message.answer("Отменить отклик?🧐", reply_markup=markup)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/confirm_end_respond"], IsHaveDataFilter())
async def confirm_end(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    split_data = callback.data.split(',')
    index = int(split_data[1])

    await callback.message.delete()
    await overallFunctions.deleteSendMessage(data["show_respond"])

    respond_data = data["responds_data"][index]
    user_data = data["user_data"]

    task = asyncio.create_task(executorFunctions.end_respond(data={"order_id": respond_data["id"],
                                                                   "user_id": user_data["id"]}))

    await task

    if task.done():
        markup = await distrubMarkups.create_back_after_actions_markup(index=0)
        send_message = await callback.message.answer("Отклик отменен🧹", reply_markup=markup)

        await state.update_data(show_respond=send_message)
    else:
        await callback.message.answer(text="❌Что-то пошло не так при работе с базой данных❌")


@router.callback_query(CallBackFilter(commands="/cancel_end_respond"), IsHaveDataFilter())
async def cancel_end(callback: CallbackQuery):
    await callback.message.delete()
