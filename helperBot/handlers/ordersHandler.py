import asyncio

import aiogram.exceptions

from aiogram import Router

from aiogram.types import Message, CallbackQuery

from aiogram.fsm.context import FSMContext

from aiogram.fsm.state import State, StatesGroup

from filters.filters import InRangeFilter, CheckRegFilter, CallBackFilter, IsHaveDataFilter, IsModuleCommands

from DataBase import usersFunctions, generalFunctions

from function import overallFunctions

from markups import distrubMarkups

router = Router()

router.message.filter(CheckRegFilter(), IsModuleCommands(commands=["/orders"]))


class RatesStates(StatesGroup):
    user_link = State()
    rate = State()
    review = State()


@router.callback_query(CallBackFilter(commands="/orders"), IsHaveDataFilter())
async def show_user_orders_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    await overallFunctions.update_user_info(message=callback.message)

    await state.update_data(page_orders=0, is_forward=True, is_first=True)

    asyncio.create_task(show_user_orders(callback.message, state))


async def prepare_text(data: dict):
    text = f"<b>Показаны заказы пользователя:</b>\n"

    for order in data:
        text = text + f"<b>Заказ №{order['id']}:</b>\n" \
                      f"Предмет: <b>{order['subject']}</b>\n" \
                      f"Тип работы: <b>{order['work_type']}</b>\n"
    return text


async def show_user_orders(message: Message, state: FSMContext):
    data = await state.get_data()

    task = asyncio.create_task(usersFunctions.get_user_orders(data=data))

    await task

    if task.done():
        result = task.result()

        if result["orders"]:
            if "page" in data:
                await overallFunctions.deleteSendMessage(data["page"])

            text = await prepare_text(data=result["orders"])

            markup = await distrubMarkups.create_orders_markup(orders=result["orders"],
                                                               is_first=data["is_first"],
                                                               is_more_take=result["is_more_take"],
                                                               is_forward=data["is_forward"])

            try:
                send_message = await message.edit_text(text=text, reply_markup=markup.as_markup())
            except aiogram.exceptions.TelegramBadRequest:
                send_message = await message.answer(text=text, reply_markup=markup.as_markup())

            await state.update_data(page=send_message, page_orders=result["page_orders"])

        else:
            if not data["page_orders"]:
                text = "У тебя нет активных заказов, создай новый заказ с помощью команды '/create'!"

                send_message = await message.answer(text=text)
                await state.update_data(page=send_message)

    else:
        await message.answer(text="❌Что-то пошло не так при работе с базой данных, попробуй позже")


@router.callback_query(lambda query: query.data.split(",")[0] in ["/user_orders"], IsHaveDataFilter())
async def orders_mover(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    is_first = False
    is_forward = bool(int(callback.data.split(',')[1]))

    if not is_forward and data["page_orders"] <= 1:
        is_forward = True
        data["page_orders"] = 0
        is_first = True

    await state.update_data(user_id=callback.message.chat.id,
                            page_orders=data["page_orders"],
                            is_forward=is_forward,
                            is_first=is_first)

    asyncio.create_task(show_user_orders(callback.message, state))


@router.callback_query(CallBackFilter(commands="/orders_back"), IsHaveDataFilter())
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    data["is_forward"] = False

    data.pop("order_data")
    data.pop("from_call")

    await state.set_data(data=data)

    asyncio.create_task(show_user_orders(message=callback.message, state=state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/order"], IsHaveDataFilter())
async def preparing_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if "page" in data:
        await overallFunctions.deleteSendMessage(data["page"])

    split_data = callback.data.split(',')

    order_data = await generalFunctions.getOrder(data={"id": split_data[1]})

    await state.update_data(user_id=callback.message.chat.id, order_data=order_data)

    asyncio.create_task(order_menu(callback.message, state))


async def order_menu(message: Message, state: FSMContext):
    data = await state.get_data()

    order_text = await overallFunctions.createOrderList(order_data=data["order_data"], is_full=True, with_number=True)

    message_1 = await message.answer(text=order_text)
    message_list = [message_1]

    media = await overallFunctions.createMediaMessages(order_data=data["order_data"])

    if media:
        message_2 = await message.answer_media_group(media=media)
        await state.update_data(photos=message_2)
        message_list.append(message_2)

    markup = await distrubMarkups.create_order_markup()
    message_3 = await message.answer(text="Что хочешь сделать с заказом?", reply_markup=markup)
    message_list.append(message_3)

    await state.update_data(page=message_list, from_call="Menu", page_tenders=0)


@router.callback_query(CallBackFilter(commands="/show_order_menu"), IsHaveDataFilter())
async def order_menu_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await overallFunctions.deleteSendMessage(data["page"])

    data.pop("page")
    data.pop("offers_page")

    data["from_call"] = "Menu"
    data["page_tenders"] = 0

    await state.set_data(data=data)

    asyncio.create_task(order_menu(callback.message, state))


async def create_title_text(order_data: dict):
    text = f"<b>Показаны отклики по заказу №{order_data['id']}</b>\n" \
           f"Предмет: <b>{order_data['subject']}</b>\n" \
           f"Тип работы: <b>{order_data['work_type']}</b>\n"\
           f"Ваша стоимость: <b>{order_data['price']}</b>\n"

    return text


async def send_title_message(callback: CallbackQuery, data: dict):
    messages_list = []

    if "offers_page" not in data:
        await overallFunctions.deleteSendMessage(data["page"])

        markup = await distrubMarkups.create_order_menu_markup()

        title_text = await create_title_text(order_data=data["order_data"])

        title_message = await callback.message.answer(text=title_text, reply_markup=markup)

        messages_list.append(title_message)
    else:
        await overallFunctions.deleteSendMessage(data=data["offers_page"])

        messages_list.append(data["page"][0])

    data["page"] = messages_list

    return data


async def send_messages(callback: CallbackQuery, data: dict, result: dict):
    messages_list = []
    offers_messages = []

    for executor in result["executors"]:

        executor_text = await overallFunctions.showUserData(data=executor, from_call="executor")

        markup = None

        if executor['rate_count'] > 0:
            markup = await distrubMarkups.create_show_review_markup(user_id=executor["id"])

        executor_message = await callback.message.answer(text=executor_text, reply_markup=markup)

        offers_messages.append(executor_message)

    messages_list.append(offers_messages)

    data["page_tenders"] = result["page_tenders"]

    data["offers_page"] = offers_messages

    data["page"].append(offers_messages)

    return data


@router.callback_query(lambda query: query.data.split(",")[0] in ["/show_tenders"], IsHaveDataFilter())
async def show_tenders(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await overallFunctions.prepareForShow(callback=callback, state=state)

    task = asyncio.create_task(usersFunctions.get_order_tenders(data=data))

    await task

    if task.done():
        data = await send_title_message(callback=callback, data=data)

        result = task.result()

        if result["executors"]:

            data = await send_messages(callback=callback, data=data, result=result)

            markup = await distrubMarkups.create_page_mover_markup(index=0,
                                                                   is_forward=data["is_forward"],
                                                                   is_more_take=result["is_more_take"],
                                                                   is_first=data["is_first"])
            if markup:
                message_2 = await callback.message.answer(text="Показать еще отклики?", reply_markup=markup)
                data["offers_page"].append(message_2)

        else:
            absence_message = await callback.message.answer(text="На заказ нет откликов😭")
            data["page"].append(absence_message)

        await state.update_data(data)

    else:
        await callback.message.answer(text="❌Что-то пошло не так при работе с базой данных❌")


@router.callback_query(CallBackFilter(commands="/order_rate_back"), IsHaveDataFilter())
async def orders_back_rate(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    data.pop("user_data")
    data.pop("rating_page")
    data.pop("page_rating")

    data["page_tenders"] -= 1

    if data["page_tenders"] <= 0:
        data["is_first"] = True

    await state.set_data(data=data)

    asyncio.create_task(show_tenders(callback=callback, state=state))


@router.callback_query(CallBackFilter(commands="/end_order"), IsHaveDataFilter())
async def end_order(callback: CallbackQuery):
    markup = await distrubMarkups.create_end_order_markup()

    await callback.message.answer("Завершить заказ?🧐", reply_markup=markup)


@router.callback_query(CallBackFilter(commands="/confirm_end"), IsHaveDataFilter())
async def confirm_end(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await overallFunctions.deleter(callback.message)
    await overallFunctions.deleteSendMessage(data["page"])

    task = asyncio.create_task(usersFunctions.end_order(data=data["order_data"]))

    await task
    if task.done():
        markup = await distrubMarkups.create_is_rate_markup()
        await callback.message.answer("Заказ завершен, хотите оценить исполнителя?🥹", reply_markup=markup)
    else:
        await callback.message.answer(text="❌Что-то пошло не так при работе с базой данных❌")


@router.callback_query(CallBackFilter(commands="/cancel_end"), IsHaveDataFilter())
async def cancel_end(callback: CallbackQuery):
    await overallFunctions.deleter(callback.message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/isRate"], IsHaveDataFilter())
async def rate_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    is_rate = bool(int(callback.data.split(",")[1]))

    if is_rate:
        asyncio.create_task(first_step_mover(callback.message, state))
    else:
        await state.clear()


async def first_step_mover(message: Message, state: FSMContext):
    await state.set_state(RatesStates.user_link)

    send_message = await message.answer(text="1️⃣<b>Введите ссылку на пользователя</b>\n "
                                             "Ее можно найти, нажав на профиль "
                                             "собеседника.\n "
                                             "Она должна начинаться с символа '@'.")

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=send_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(RatesStates.user_link)
async def first_step(message: Message, state: FSMContext):
    await message.delete()

    text = message.text

    await state.update_data(user_link=text)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


async def second_step_mover(message: Message, state: FSMContext):
    await state.set_state(RatesStates.rate)

    send_message = await message.answer(text="2️⃣<b>Введите оценку исполнителя от 1 до 5?</b>")

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=send_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(RatesStates.rate, InRangeFilter(1, 5))
async def second_step(message: Message, state: FSMContext):
    await message.delete()

    text = message.text

    await state.update_data(rate=int(text))

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(RatesStates.rate)
async def second_step_error(message: Message, state: FSMContext):
    data = await state.get_data()

    send_message = await message.answer(text="2️⃣❌Введите оценку числом от 1 до 5❌")

    if isinstance(data["page"], list):
        data["page"].append(send_message)
    else:
        data["page"] = [data["page"], send_message]

    await state.update_data(page=data["page"])


async def third_step_mover(message: Message, state: FSMContext):
    await state.set_state(RatesStates.review)

    send_message = await message.answer(text="3️⃣<b>Напишите отзыв об исполнителе, об качестве и скорости "
                                             "проделанной работе.\n</b>"
                                             "Если нечего сказать, то пропустите этот этап.")

    text = await overallFunctions.getText(state=state)
    if not text:
        await state.update_data(page=send_message, review="-")

    await state.update_data(page=send_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(RatesStates.review)
async def third_step(message: Message, state: FSMContext):
    await message.delete()

    text = message.text

    await state.update_data(review=text)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


async def take_text(add_text: str, message: Message, state: FSMContext):
    data = await state.get_data()

    message_text = f"<b>Введенное значение:</b>\t{str(add_text)}"

    markup_func = distrubMarkups.create_corrected_markup if "correcting" in data else distrubMarkups.create_mover_markup

    markup = await markup_func(is_text=True, index=2)

    if "media_message" in data and data["media_message"]:
        await overallFunctions.deleteSendMessage(data["media_message"])

    media_message = await message.answer(text=message_text, reply_markup=markup)

    await state.update_data(media_message=media_message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/cancel_rate_choose"], IsHaveDataFilter())
async def cancel_input(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    active_state = (await state.get_state()).split(':')[1]

    try:
        data.pop(active_state)

        await state.set_data(data)

        asyncio.create_task(take_text(add_text="", message=callback.message, state=state))

    except KeyError:
        pass


@router.callback_query(CallBackFilter(commands="/next_step_rate"), IsHaveDataFilter())
async def next_step(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    active_state = (await state.get_state()).split(':')[1]
    message = callback.message

    try:
        input_media = data[active_state]
    except KeyError:
        input_media = None

    if input_media or active_state == "review":
        await overallFunctions.deleteSendMessage(data["page"])
        if data["media_message"] is not None:
            await state.update_data(media_message=None)
            await overallFunctions.deleteSendMessage(data["media_message"])

        if active_state == "user_link":
            if "correcting" not in data:
                asyncio.create_task(second_step_mover(message=message, state=state))

        elif active_state == "rate":
            if "correcting" not in data:
                asyncio.create_task(third_step_mover(message=message, state=state))

        elif active_state == "review":
            if "correcting" not in data:
                asyncio.create_task(show_data(message=message, state=state))

        if "correcting" in data:
            asyncio.create_task(show_data(message=message, state=state))


@router.callback_query(CallBackFilter(commands="/back_step_rate"), IsHaveDataFilter())
async def previous_step(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    data = await state.get_data()

    message = callback.message

    await overallFunctions.deleteSendMessage(data["page"])
    active_state = (await state.get_state()).split(':')[1]

    if active_state == "rate" or "user_link":
        asyncio.create_task(first_step_mover(message=message, state=state))

    elif active_state == "review":
        asyncio.create_task(second_step_mover(message=message, state=state))


async def show_data(message: Message, state: FSMContext):
    await state.set_state(state=None)

    message_text = await overallFunctions.showRateData(state)

    markup = await distrubMarkups.create_is_correct_markup(index=1)

    send_message = await message.answer(text=message_text, reply_markup=markup)

    await state.update_data(page=send_message)


@router.callback_query(CallBackFilter(commands='/rate_correct'), IsHaveDataFilter())
async def rateUser(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await overallFunctions.deleteSendMessage(data["page"])

    task = asyncio.create_task(usersFunctions.rate_user(data={"user_link": data['user_link'],
                                                              "rate_user": callback.message.chat.id,
                                                              "order_id": data["order_data"]["id"],
                                                              "rate": data["rate"],
                                                              "review": data["review"]}))

    await task

    if task.done():
        markup = await distrubMarkups.create_back_after_actions_markup(index=1)

        if task.result():
            await callback.message.answer(text="✅Пользователь оценен!✅", reply_markup=markup)
        else:
            await callback.message.answer(text="❌Я не смог оценить этого пользователя❌", reply_markup=markup)
    else:
        await callback.message.answer(text="❌К сожалению произошла ошибка и пользователь не был оценен😢❌")


@router.callback_query(CallBackFilter(commands='/rateNotCorrect'), IsHaveDataFilter())
async def rate_user(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await overallFunctions.deleteSendMessage(data["page"])

    await state.update_data(correcting=True)

    builder = await distrubMarkups.create_choose_fix_markup(index=2)
    send_message = await callback.message.answer(text="<b>Выбери параметр, который хочешь изменить</b>",
                                                 reply_markup=builder.as_markup())

    await state.update_data(page=send_message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/rate_correct"], IsHaveDataFilter())
async def change_values(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    command = await overallFunctions.getCallbackText(callback=callback)

    if command == "Имя":
        asyncio.create_task(first_step_mover(message=callback.message, state=state))

    elif command == "Оценка":
        asyncio.create_task(second_step_mover(message=callback.message, state=state))

    elif command == "Отзыв":
        asyncio.create_task(third_step_mover(message=callback.message, state=state))
