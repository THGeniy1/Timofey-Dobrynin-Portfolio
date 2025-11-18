import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from filters.filters import CheckRegFilter, CallBackFilter, IsHaveDataFilter, IsModuleCommands, PriceFilter
from DataBase import executorFunctions, generalFunctions
from function import overallFunctions
from markups import distrubMarkups

router = Router()

router.message.filter(CheckRegFilter(), IsModuleCommands(commands=["/show"]))


class Order(StatesGroup):
    work_types = State()
    categories = State()
    subjects = State()
    price = State()


async def create_title_text(data: dict, is_pre_show: bool):
    texts = {"cities": '-', "universities": '-', "work_types": '-', "categories": '-', "subjects": '-'}

    for text in texts:
        if text in data and data[text]:
            texts[text] = ',\t'.join(data[text])

    if is_pre_show:
        text = "<b>Показать заказы по следующим фильтрам?</b>\n"
    else:
        text = "<b>🔧Показаны заказы по следующим фильтрам:🔧</b>\n"

    text = text + f"-Категории наук:\t<b>{texts['categories']}</b>\n" \
                  f"-Типы заданий:\t<b>{texts['work_types']}</b>\n" \
                  f"-Предметы:\t<b>{texts['subjects']}</b>"

    return text


@router.message(Command(commands='show', prefix='/'))
async def show_order_command(message: Message, state: FSMContext):
    await message.delete()

    await overallFunctions.clearOld(state=state)
    await overallFunctions.update_user_info(message=message)

    data = {"work_types": [], "categories": [], "subjects": [], "filter": "0,1",
            "is_forward": True, "is_first": True, "page_count": 0}

    await state.set_data(data)

    asyncio.create_task(show_orders(message=message, state=state))


async def first_step_mover(message: Message, state: FSMContext):
    await state.set_state(Order.categories)

    builder = await distrubMarkups.create_science_markup(start_index=0,
                                                         is_forward=True,
                                                         mover_index=1)

    category_message = await message.answer(text="1️⃣<b>Выберите категории, по которым хотите посмотреть заказы</b>\n\n"
                                                 "Если затрудняетесь с выбором категорий, вызовите команду\t"
                                                 "/instruction",
                                            reply_markup=builder.as_markup())

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=category_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/exec_science_move"], IsHaveDataFilter())
async def change_categories(callback: CallbackQuery, state: FSMContext):
    split_data = callback.data.split(',')

    is_forward = bool(int(split_data[1]))
    start_index = int(split_data[2])

    builder = await distrubMarkups.create_science_markup(start_index=start_index,
                                                         is_forward=is_forward,
                                                         mover_index=1)

    if builder:
        category_message = await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

        await state.update_data(page=category_message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/executor_science"], IsHaveDataFilter())
async def first_step(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    text = await overallFunctions.getCallbackText(callback=callback)

    if text not in data["categories"]:
        data["categories"].append(text)

        await state.update_data(category=data["categories"])

    text = ", ".join(data["categories"])

    asyncio.create_task(take_text(add_text=text, message=callback.message, state=state))


async def second_step_mover(message: Message, state: FSMContext):
    await state.set_state(Order.work_types)
    data = await state.get_data()

    builder = await distrubMarkups.create_types_markup(start_index=0,
                                                       categories=data["categories"],
                                                       is_forward=True,
                                                       mover_index=1)

    type_message = await message.answer(text="2️⃣<b>Выберите типы работ, по которым показать заказы</b>\n\n"
                                             "Если нет нужного типа задания, то вызовите команду /help,\t"
                                             "там вы найдете форму в которой можете попросить добавить\t"
                                             "нужный тип задания",

                                        reply_markup=builder.as_markup())

    text = await overallFunctions.getText(state=state)

    await state.update_data(page=type_message)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/exec_work_move"], IsHaveDataFilter())
async def change_works(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    split_data = callback.data.split(',')

    is_forward = bool(int(split_data[1]))
    start_index = int(split_data[2])

    builder = await distrubMarkups.create_types_markup(start_index=start_index,
                                                       categories=data["categories"],
                                                       is_forward=is_forward,
                                                       mover_index=1)
    if builder:
        send_message = await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

        await state.update_data(page=send_message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/take_media"], IsHaveDataFilter())
async def second_step(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    text = await overallFunctions.getCallbackText(callback=callback)

    if text not in data["work_types"]:
        data["work_types"].append(text)

        await state.update_data(work_types=data["work_types"])

    text = ", ".join(data["work_types"])

    asyncio.create_task(take_text(add_text=text, message=callback.message, state=state))


async def third_step_mover(message: Message, state: FSMContext):
    await state.set_state(Order.subjects)

    subject_message = await message.answer(text="3️⃣<b>Введите наименования предметов по которым\t"
                                                "хотите увидеть заказы</b>")

    await state.update_data(page=subject_message)

    text = await overallFunctions.getText(state=state)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(Order.subjects)
async def third_step(message: Message, state: FSMContext):
    await message.delete()

    data = await state.get_data()

    texts = message.text.split(',')

    for text in texts:
        if text not in data["subjects"]:
            data["subjects"].append(text)

            await state.update_data(subjects=data["subjects"])

    text = ", ".join(data["subjects"])

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


async def take_text(add_text: str, message: Message, state: FSMContext):
    data = await state.get_data()

    message_text = "<b>Введенные значения:</b>\t" + add_text

    if "price" in data:
        markup = await distrubMarkups.create_reg_respond_markup()
    else:
        markup = await distrubMarkups.create_corrected_markup(is_text=True, index=1)

    if "media_message" in data and data["media_message"]:
        await overallFunctions.deleteSendMessage(data["media_message"])

    media_message = await message.answer(text=message_text, reply_markup=markup)

    await state.update_data(media_message=media_message)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/cancel_exec_choose"], IsHaveDataFilter())
async def cancel_input(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    active_state = (await state.get_state()).split(':')[1]

    try:
        if isinstance(data[active_state], list):
            data[active_state].pop(-1)

        elif isinstance(data[active_state], str):
            data[active_state] = None

        else:
            keys = list(data[active_state])

            data[active_state].pop(keys[-1])

        await state.set_data(data)

        try:
            text = ', '.join(data[active_state])
        except TypeError:
            text = ''

        asyncio.create_task(take_text(add_text=text, message=callback.message, state=state))

    except KeyError and IndexError:
        pass


@router.callback_query(CallBackFilter(commands="/next_step_exec"), IsHaveDataFilter())
async def next_step(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    active_state = (await state.get_state()).split(':')[1]
    message = callback.message

    try:
        input_media = data[active_state]
    except KeyError:
        input_media = None

    if active_state == 'price':
        if input_media:
            await overallFunctions.deleteSendMessage(data=data["respond_page"])
            await overallFunctions.deleteSendMessage(data=data["media_message"])

            await register_respond(message=message, state=state)

    else:
        await overallFunctions.deleteSendMessage(data["page"])

        if data["media_message"] is not None:
            await state.update_data(media_message=None)
            await overallFunctions.deleteSendMessage(data["media_message"])

        asyncio.create_task(pre_show_data(message=message, state=state))


async def pre_show_data(message: Message, state: FSMContext):
    data = await state.get_data()

    markup = await distrubMarkups.create_is_correct_filter()

    title_text = await create_title_text(data=data, is_pre_show=True)

    title_message = await message.answer(text=title_text, reply_markup=markup)

    await state.update_data(page=title_message, page_count=0)


async def send_title_message(message: Message, data: dict):
    messages_list = []

    if "offers_page" not in data or not data["offers_page"]:
        if "page" in data:
            await overallFunctions.deleteSendMessage(data["page"])

        markup = await distrubMarkups.create_filters_markup()

        title_text = await create_title_text(data=data, is_pre_show=False)

        title_message = await message.answer(text=title_text, reply_markup=markup)

        messages_list.append(title_message)
    else:
        await overallFunctions.deleteSendMessage(data=data["offers_page"])

        messages_list.append(data["page"][0])

    data["page"] = messages_list

    return data


async def send_messages(message: Message, data: dict, result: dict):
    offers_messages = []

    for order in result["orders"]:
        order_text = await overallFunctions.createOrderList(order_data=order, is_full=False, with_number=False)
        markup = await distrubMarkups.create_show_order_markup(order_data=order)

        message_1 = await message.answer(text=order_text, reply_markup=markup)
        offers_messages.append(message_1)

    markup = await distrubMarkups.create_page_mover_markup(index=1,
                                                           is_forward=data["is_forward"],
                                                           is_more_take=result["is_more_take"],
                                                           is_first=data["is_first"])

    if markup:
        message_2 = await message.answer(text="Показать еще заказы?", reply_markup=markup)
        offers_messages.append(message_2)

    data["page_count"] = result["page_count"]

    data["offers_page"] = offers_messages

    data["page"].append(offers_messages)

    return data


@router.callback_query(lambda query: query.data.split(",")[0] in ["/show_orders"], IsHaveDataFilter())
async def callback_show_orders(callback: CallbackQuery, state: FSMContext):
    await overallFunctions.prepareForShow(callback=callback, state=state)
    asyncio.create_task(show_orders(message=callback.message, state=state))


async def show_orders(message: Message, state: FSMContext):
    data = await state.get_data()

    task = asyncio.create_task(executorFunctions.getOrders(data=data))

    await task

    if task.done():
        data = await send_title_message(message=message, data=data)

        result = task.result()

        if result["orders"]:
            data = await send_messages(message=message, data=data, result=result)

        else:
            absence_message = await message.answer(text="По выбранным фильтрам заказов нет🤷‍")
            data["page"].append(absence_message)

        await state.set_data(data)

    else:
        await message.answer(text="❌Что-то пошло не так при работе с базой данных❌")


@router.callback_query(CallBackFilter(commands="/change_filters"), IsHaveDataFilter())
async def change_filters(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await overallFunctions.deleteSendMessage(data["page"])

    builder = await distrubMarkups.create_choose_fix_markup(index=1)

    send_message = await callback.message.answer(text="<b>Выберите фильтр, который хотите изменить</b>",
                                                 reply_markup=builder.as_markup())

    await state.update_data(page=send_message, offers_page=None)


@router.callback_query(lambda query: query.data.split(",")[0] in ["/executor_correct"], IsHaveDataFilter())
async def change_values(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    command = await overallFunctions.getCallbackText(callback=callback)

    await state.update_data(correcting=True)

    if command == "Категории":
        asyncio.create_task(first_step_mover(callback.message, state))

    elif command == "Типы Заданий":
        asyncio.create_task(second_step_mover(callback.message, state))

    elif command == "Предметы":
        asyncio.create_task(third_step_mover(callback.message, state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/filter"], IsHaveDataFilter())
async def change_filter(callback: CallbackQuery, state: FSMContext):
    split_data = callback.data.split(',')
    data = await state.get_data()

    if split_data[1] == "0":
        orders_filter = "0,1"
    else:
        filter_data = data["filter"].split(',')

        if split_data[1] != filter_data[0] or filter_data[1] == "2":
            value = "1"
        else:
            value = "2"

        orders_filter = f"{split_data[1]},{value}"

    if data["page_count"] > 0:
        page = data["page_count"] - 1
    else:
        page = data["page_count"]

    await state.update_data(filter=orders_filter, page_count=page)

    asyncio.create_task(show_orders(message=callback.message, state=state))


@router.callback_query(lambda query: query.data.split(",")[0] in ["/show_order"], IsHaveDataFilter())
async def show_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await overallFunctions.deleteSendMessage(data=data["page"])

    split_data = callback.data.split(',')

    order_id = split_data[1]

    task = asyncio.create_task(generalFunctions.getOrder(data={"id": order_id}))

    await task

    if task.done():
        order_data = task.result()

        order_text = await overallFunctions.createOrderList(order_data=order_data, is_full=True, with_number=True)

        message_1 = await callback.message.answer(text=order_text)
        message_list = [message_1]

        media = await overallFunctions.createMediaMessages(order_data=order_data)

        if media:
            message_2 = await callback.message.answer_media_group(media=media)
            message_list.append(message_2)

        markup = await distrubMarkups.create_respond_markup()
        message_3 = await callback.message.answer(text="Что хочешь сделать?", reply_markup=markup)
        message_list.append(message_3)

        await state.update_data(show_order=message_list, order_data=order_data)
    else:
        await callback.message.answer(text="❌Что-то пошло не так при работе с базой данных❌")


@router.callback_query(CallBackFilter(commands="/respond"), IsHaveDataFilter())
async def respond_to_order(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Order.price)

    send_message = await callback.message.answer(text="<b>💸Введите стоимость за которую вы готовы выполнить\t"
                                                      "данную работу💸</b>")

    text = await overallFunctions.getText(state=state)

    await state.update_data(respond_page=send_message, price=None)

    asyncio.create_task(take_text(add_text=text, message=callback.message, state=state))


@router.message(Order.price, PriceFilter())
async def price_step(message: Message, state: FSMContext):
    await message.delete()

    text = message.text

    await state.update_data(price=text)

    asyncio.create_task(take_text(add_text=text, message=message, state=state))


@router.message(Order.price)
async def error_price_step(message: Message, state: FSMContext):
    await message.delete()

    data = await state.get_data()

    send_message = await message.answer(text="❌Вы указали стоимость не в рублях")

    if isinstance(data["respond_page"], list):
        data["respond_page"].append(send_message)
    else:
        data["respond_page"] = [data["respond_page"], send_message]

    await state.update_data(respond_page=data["respond_page"])


async def register_respond(message: Message, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()

    task = asyncio.create_task(executorFunctions.add_respond(data=[data["order_data"]["id"],
                                                                   message.chat.id,
                                                                   int(data["price"])]))

    await task

    if task.done():

        if isinstance(task.result(), dict):
            text = f"🔆Отклик на заказ №{data['order_data']['id']} зарегистрирован🔆"
        else:
            text = f"⚠Вы уже откликались на этот заказ⚠"

    else:
        text = "❌Что-то пошло не так при работе с базой данных, попробуй позже"

    send_message = await message.answer(text=text)

    data["show_order"].append(send_message)

    data.pop("price")
    data.pop("respond_page")

    await state.set_data(data=data)


@router.callback_query(CallBackFilter(commands="/return_show"), IsHaveDataFilter())
async def return_show(callback: CallbackQuery, state: FSMContext):
    def Text(split_text: list[str]):
        new_text = ""
        for split_index, splits in enumerate(split_text):
            if split_index % 2 == 0:
                splits = f"<b>{splits}</b>"
            new_text = new_text + f"{splits}\n"
        return new_text

    async def send_message(message: Message):
        text = message.text
        split_text = text.split('\n')
        print("split text", split_text)
        if len(split_text) == 9:
            text = Text(split_text=split_text)
        elif len(split_text) == 3:
            split_text[0] = f"<b>{split_text[0]}</b>"
            text = '\n'.join(split_text)

        markup = message.reply_markup

        folds_message = await callback.message.answer(text=text, reply_markup=markup)

        return folds_message

    message_list = []
    offers_list = []

    data = await state.get_data()

    shows_order = data.pop("show_order")
    data.pop("order_data")

    await state.set_data(data=data)
    await overallFunctions.deleteSendMessage(data=shows_order)

    for value in data["page"]:
        if not isinstance(value, list):
            new_message = await send_message(message=value)

            message_list.append(new_message)
        else:
            for mes in value:
                new_message = await send_message(message=mes)
                offers_list.append(new_message)

            message_list.append(offers_list)

    await state.update_data(page=message_list, offers_page=offers_list)
