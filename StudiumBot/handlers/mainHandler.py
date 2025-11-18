import asyncio

from typing import Union
from aiogram import Router
from Other import Texts

from aiogram.filters import Command
from filters.middlewares import album_middleware

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import Message, CallbackQuery

from DataBase import usersFunctions

from markups import distrubMarkups
from function import overallFunctions
from filters.filters import CallBackFilter, CheckRegFilter, PriceFilter, IsHaveDataFilter, IsModuleCommands

router = Router()

router.message.middleware(album_middleware)

router.message.filter(CheckRegFilter(), IsModuleCommands(commands=["/create"]))


class OrderStates(StatesGroup):
    subject = State()
    work_type = State()
    category = State()
    photos = State()
    order_condition = State()
    price = State()
    deleting = State()


@router.message(Command(commands='create', prefix='/'))
async def start_new_order(message: Message, state: FSMContext):
    await message.delete()

    await overallFunctions.clearOld(state=state)
    await overallFunctions.update_user_info(message=message)

    await state.update_data(user_id=message.chat.id, from_call="Creating")

    asyncio.create_task(first_step_mover(message=message, state=state))


async def first_step_mover(message: Message, state: FSMContext):
    await state.set_state(OrderStates.subject)

    send_message = await message.answer(text="1️⃣<b>Введите наименование предмета,\t"
                                             "по которому нужно выполнить работу</b>")

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=send_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(OrderStates.subject)
async def first_step(message: Message, state: FSMContext):
    await message.delete()

    text = message.text

    await state.update_data(subject=text)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


async def second_step_mover(message: Message, state: FSMContext):
    await state.set_state(OrderStates.category)

    await state.update_data(work_type=None)

    builder = await distrubMarkups.create_science_markup(start_index=0, is_forward=True, mover_index=0)

    send_message = await message.answer(text="2️⃣<b>Выберите категорию, к которой относится ваш предмет</b>\n\n"
                                             "Если затрудняетесь с выбором категории, вызовите команду /instruction",
                                        reply_markup=builder.as_markup())

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=send_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/science_move"], IsHaveDataFilter())
async def change_categories(callback: CallbackQuery, state: FSMContext):
    split_data = callback.data.split(',')

    is_forward = bool(int(split_data[1]))
    start_index = int(split_data[2])

    builder = await distrubMarkups.create_science_markup(start_index=start_index, is_forward=is_forward, mover_index=0)
    if builder:
        send_message = await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

        await state.update_data(page=send_message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/science"], IsHaveDataFilter())
async def second_step(callback: CallbackQuery, state: FSMContext):
    text = await overallFunctions.getCallbackText(callback=callback)

    await state.update_data(category=text)

    asyncio.create_task(take_text(add_text=text, message=callback.message, state=state))


async def third_step_mover(message: Message, state: FSMContext):
    await state.set_state(OrderStates.work_type)
    data = await state.get_data()

    builder = await distrubMarkups.create_types_markup(start_index=0,
                                                       categories=data["category"],
                                                       is_forward=True,
                                                       mover_index=0)

    send_message = await message.answer(text="3️⃣<b>Выберите тип задания, который нужно выполнить</b>\n\n"
                                             "Если нет нужного типа задания, то вызовите команду /help,\t"
                                             "там вы найдете форму в которой можете попросить добавить\t"
                                             "нужный тип задания",
                                        reply_markup=builder.as_markup())

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=send_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/work_move"], IsHaveDataFilter())
async def change_works(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    split_data = callback.data.split(',')

    is_forward = bool(int(split_data[1]))
    start_index = int(split_data[2])

    builder = await distrubMarkups.create_types_markup(start_index=start_index,
                                                       categories=data["category"],
                                                       is_forward=is_forward,
                                                       mover_index=0)
    if builder:
        send_message = await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

        await state.update_data(page=send_message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/reg_type"], IsHaveDataFilter())
async def third_step(callback: CallbackQuery, state: FSMContext):
    text = await overallFunctions.getCallbackText(callback=callback)

    await state.update_data(work_type=text)

    asyncio.create_task(take_text(add_text=text, message=callback.message, state=state))


async def fourth_step_mover(message: Message, state: FSMContext):
    await state.set_state(OrderStates.photos)

    send_message = await message.answer(text="4️⃣<b>Отправьте до 10 фотографий с информацией необходимой для "
                                             "выполнения заказа.\n\n"
                                             "Фотографии помогут потенциальным исполнителям лучше\t"
                                             "понять, что предстоит выполнить,\t"
                                             "а вам найти более компетентного исполнителя.\n\n"
                                             "Если фотографий нет, то можете пропустить этот этап</b>")
    await state.update_data(page=send_message)

    asyncio.create_task(take_media(message=message, state=state))


@router.message(OrderStates.photos)
async def fourth_step(message: Message, state: FSMContext):
    asyncio.create_task(take_media(message=message, state=state))


async def fifth_step_mover(message: Message, state: FSMContext):
    await state.set_state(OrderStates.order_condition)

    send_message = await message.answer(text="5️⃣<b>Напишите описание, которое расскажет исполнителям об предстоящей "
                                             "работе.\n\nРасскажите что им предстоит выполнить, что изображено на\t"
                                             "фотографиях, какие сроки и какие могут возникнут трудности.\n\n"
                                             "Это поможет быстрее и качественнее найти исполнителей.</b>")

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=send_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(OrderStates.order_condition)
async def fifth_step(message: Message, state: FSMContext):
    await message.delete()

    text = message.text

    await state.update_data(order_condition=text)

    asyncio.create_task(take_text(add_text=message.text, message=message, state=state))


async def sixth_step_mover(message: Message, state: FSMContext):
    await state.set_state(OrderStates.price)

    data = await state.get_data()

    send_message = await message.answer(text="6️⃣<b>Укажите примерную стоимость, на которую вы рассчитываете.\n\n"
                                             "Минимальная стоимость на этот тип работ составляет:\t"
                                             f"{Texts.types_list[data['work_type']]}</b>\n\n"
                                             "Конечную стоимость можно будет обсудить с исполнителем.")

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=send_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(OrderStates.price, PriceFilter())
async def sixth_step(message: Message, state: FSMContext):
    await message.delete()

    text = message.text

    await state.update_data(price=text)

    asyncio.create_task(take_text(add_text=message.text, message=message, state=state))


@router.message(OrderStates.price)
async def error_price_step(message: Message, state: FSMContext):
    await message.delete()

    data = await state.get_data()

    send_message = await message.answer(text="❌Вы указали стоимость не в рублях или же меньше минимального значения")

    if isinstance(data["page"], list):
        data["page"].append(send_message)
    else:
        data["page"] = [data["page"], send_message]

    await state.update_data(page=data["page"])


async def take_text(add_text: str, message: Message, state: FSMContext):
    data = await state.get_data()

    message_text = f"<b>Введенное значение:</b>\t{str(add_text)}"

    markup_func = distrubMarkups.create_corrected_markup if "correcting" in data else distrubMarkups.create_mover_markup

    markup = await markup_func(is_text=True, index=0)

    if "media_message" in data and data["media_message"]:
        await overallFunctions.deleteSendMessage(data["media_message"])

    media_message = await message.answer(text=message_text, reply_markup=markup)

    await state.update_data(media_message=media_message)


async def take_media(message: Union[Message, None], state: FSMContext):
    data = await state.get_data()

    media_group_message = []

    if "media_message" in data and data["media_message"]:
        await overallFunctions.deleteSendMessage(data["media_message"])

    markup_func = distrubMarkups.create_corrected_markup if "correcting" in data else distrubMarkups.create_mover_markup

    markup = await markup_func(is_text=False, index=0)

    message_text = f"<b>Введенное значение:</b>"

    if "photos" in data and data["photos"]:
        if isinstance(data["photos"], str):
            media_list = await overallFunctions.createMediaMessages(order_data=data)
        else:
            media_list = await overallFunctions.createMediaList(data=data["photos"])

        if media_list:
            media_message = await message.answer_media_group(media=media_list)
            media_group_message += media_message

    media_message = await message.answer(text=message_text, reply_markup=markup)

    media_group_message.append(media_message)

    await state.update_data(media_message=media_group_message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/cancel_main_choose"], IsHaveDataFilter())
async def cancel_input(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    active_state = (await state.get_state()).split(':')[1]

    try:
        data.pop(active_state)

        await state.set_data(data)

        asyncio.create_task(take_text(add_text="", message=callback.message, state=state))

    except KeyError:
        pass


@router.callback_query(lambda query: query.data.split(",")[0] in ["/delete_media"], IsHaveDataFilter())
async def delete_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    active_state = (await state.get_state()).split(':')[1]

    if active_state in data and data[active_state]:
        await callback.message.delete()
        await overallFunctions.deleteSendMessage(data["page"])

        if isinstance(data[active_state], str):
            order_media = data[active_state].split(",")
        else:
            order_media = data[active_state]

        await state.update_data(order_media=order_media)

        send_message = await callback.message.answer(text=f"🔴<b>Введите через запятую номера фотографий,\t"
                                                          f"которые хотите удалить</b>\n"
                                                          f"Доступные номера от 1 до {len(order_media)}")

        await state.set_state(OrderStates.deleting)

        await state.update_data(active_state=active_state)
        await state.update_data(page=send_message)


@router.message(OrderStates.deleting)
async def delete_media(message: Message, state: FSMContext):
    async def convertToInt(value: str):
        try:
            return int(value)
        except ValueError:
            return None

    data = await state.get_data()

    await message.delete()

    await overallFunctions.deleteSendMessage(data["page"])

    await state.update_data(deleting=None, order_media=None)

    split_list = message.text.split(',')

    for val in split_list:
        index = await convertToInt(value=val)
        if index is not None and 0 < index <= len(data["order_media"]):
            data["order_media"][index - 1] = None

    data["order_media"] = [item for item in data["order_media"] if item is not None]

    await overallFunctions.deleteSendMessage(data["media_message"])

    if data["order_media"]:
        if isinstance(data["order_media"][0], str):
            await state.update_data(photos=','.join(data["order_media"]))
        else:
            await state.update_data(photos=data["order_media"])
    else:
        await state.update_data(photos=[])

    asyncio.create_task(fourth_step_mover(message, state))


@router.callback_query(CallBackFilter(commands="/next_step_main"), IsHaveDataFilter())
async def next_step(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    active_state = (await state.get_state()).split(':')[1]
    message = callback.message

    try:
        input_media = data[active_state]
    except KeyError:
        input_media = None

    if input_media or active_state == "photos":
        await overallFunctions.deleteSendMessage(data["page"])
        await overallFunctions.deleteSendMessage(data["media_message"])

        if active_state == "subject":
            if "correcting" not in data:
                asyncio.create_task(second_step_mover(message=message, state=state))

        elif active_state == "category":
            asyncio.create_task(third_step_mover(message=message, state=state))

        elif active_state == "work_type":
            if "correcting" not in data:
                asyncio.create_task(fourth_step_mover(message=message, state=state))
            else:
                asyncio.create_task(sixth_step_mover(message=message, state=state))

        elif active_state == "photos":
            if "correcting" not in data:
                asyncio.create_task(fifth_step_mover(message=message, state=state))

        elif active_state == "order_condition":
            if "correcting" not in data:
                asyncio.create_task(sixth_step_mover(message=message, state=state))

        elif active_state == "price":
            if "correcting" not in data:
                asyncio.create_task(show_data(message=message, state=state))

        if "correcting" in data and active_state != ("category" and "work_type"):
            asyncio.create_task(show_data(message=message, state=state))


@router.callback_query(CallBackFilter(commands="/back_step_main"), IsHaveDataFilter())
async def previous_step(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    message = callback.message

    active_state = (await state.get_state()).split(':')[1]

    await overallFunctions.deleteSendMessage(data["page"])
    await overallFunctions.deleteSendMessage(data["media_message"])

    if active_state == ("category" or "subject"):
        asyncio.create_task(first_step_mover(message=message, state=state))

    elif active_state == "work_type":
        asyncio.create_task(second_step_mover(message=message, state=state))

    elif active_state == "photos":
        asyncio.create_task(third_step_mover(message=message, state=state))

    elif active_state == "order_condition":
        if "photos" in data:
            await overallFunctions.deleteSendMessage(data["photos"])

        asyncio.create_task(fourth_step_mover(message=message, state=state))

    elif active_state == "price":
        asyncio.create_task(fifth_step_mover(message=message, state=state))


async def show_data(message: Message, state: FSMContext):
    data = await state.get_data()

    order_text = await overallFunctions.createOrderList(order_data=data, is_full=True, with_number=False)

    message_list = []

    if "correcting" not in data:
        text = "⚠Перед тем как я зарегистрирую заказ, <b>проверьте введенную по нему информацию:</b>"

    else:
        text = "⚠Перед тем как я обновлю заказ, <b>проверьте введенную по нему информацию:</b>"

    message1 = await message.answer(text=text)

    message2 = await message.answer(text=order_text)

    message_list.append(message1)

    message_list.append(message2)

    if "photos" in data and data["photos"]:
        if isinstance(data["photos"], str):
            send_photo_list = await overallFunctions.createMediaMessages(order_data=data)
        else:
            send_photo_list = await overallFunctions.createMediaList(data=data["photos"])

        if send_photo_list:
            media_message = await message.answer_media_group(media=send_photo_list)
            message_list.append(media_message)

    markup = await distrubMarkups.create_is_correct_markup(index=0)

    message5 = await message.answer(text='Введенная информация верна?', reply_markup=markup)
    message_list.append(message5)

    await state.update_data(page=message_list)


@router.callback_query(CallBackFilter(commands='/orderNotCorrect'), IsHaveDataFilter())
async def correct_registration(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await overallFunctions.deleteSendMessage(data["page"])

    if "order_data" in data:
        order_data = data["order_data"]

        order_data["from_call"] = "Menu"

        await state.set_data(data=order_data)

    builder = await distrubMarkups.create_choose_fix_markup(index=0)

    send_message = await callback.message.answer(text="<b>Выберите параметр, который хотите изменить</b>",
                                                 reply_markup=builder.as_markup())

    await state.update_data(page=send_message)


@router.callback_query(CallBackFilter(commands='/orderCorrect'), IsHaveDataFilter())
async def end_registration(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await state.clear()
    await overallFunctions.deleteSendMessage(data["page"])

    send_message = await callback.message.answer(text='⏳Заказ регистрируется в базе данных....')

    await state.update_data(page=send_message)

    data["user_id"] = callback.message.chat.id

    if data["from_call"] == "Creating":
        task = asyncio.create_task(usersFunctions.add_order(data=data))
        text = "🎉Вот и все!\n\nЗаказ зарегистрирован под номером <b>{}</b>,\t" \
               "закрыть и отредактировать его можно с помощью команды: /orders!\n\n" \
               "Если на него никто не откликнется в течение недели, он будет автоматически завершен!"
    else:
        task = asyncio.create_task(usersFunctions.update_order(data=data))
        text = "✅Информация по заказу обновлена!✅"

    await task
    await send_message.delete()

    if task.done() and isinstance(task.result(), str):
        await callback.message.answer(text=text.format(task.result()))
    else:
        await callback.message.answer(text="❌Что-то пошло не так при работе с базой данных❌")


@router.callback_query(lambda query: query.data.split(",")[0] in ["/main_correct"], IsHaveDataFilter())
async def change_values(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.update_data(correcting=True)

    command = await overallFunctions.getCallbackText(callback=callback)

    if command == "Предмет":
        asyncio.create_task(first_step_mover(callback.message, state))

    elif command == "Тип Задания":
        asyncio.create_task(third_step_mover(callback.message, state))

    elif command == "Категория":
        asyncio.create_task(second_step_mover(callback.message, state))

    elif command == "Фотографии":
        asyncio.create_task(fourth_step_mover(callback.message, state))

    elif command == "Описание":
        asyncio.create_task(fifth_step_mover(callback.message, state))

    else:
        asyncio.create_task(sixth_step_mover(callback.message, state))
