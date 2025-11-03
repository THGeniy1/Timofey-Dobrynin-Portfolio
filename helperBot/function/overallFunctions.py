import aiogram.exceptions

from typing import Union

from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile

from aiogram.fsm.context import FSMContext

from DataBase import generalFunctions


async def deleter(message: Message):
    try:
        await message.delete()

    except aiogram.exceptions.TelegramBadRequest:
        pass


async def deleteSendMessage(data: Union[list, Message]):
    if isinstance(data, list):
        for m in data:
            if isinstance(m, list):
                for subMessage in m:
                    await deleter(subMessage)
            else:
                await deleter(m)
    else:
        await deleter(data)


async def clearOld(state: FSMContext):
    data = await state.get_data()

    if "page" in data and data["page"]:
        await deleteSendMessage(data=data["page"])

    if "media_message" in data and data["media_message"]:
        await deleteSendMessage(data=data["media_message"])

    if "show_order" in data and data["show_order"]:
        await deleteSendMessage(data=data["show_order"])

    if "show_respond" in data and data["show_respond"]:
        await deleteSendMessage(data=data["show_respond"])


async def getText(state: FSMContext):
    data = await state.get_data()
    active_state = (await state.get_state()).split(':')[1]

    text = ""
    if active_state in data and data[active_state]:
        if isinstance(data[active_state], list):
            text = ',\t'.join(data[active_state])

        elif isinstance(data[active_state], dict):
            text = ',\t'.join(data[active_state].keys())

        else:
            text = data[active_state]

    return text


async def getCallbackText(callback: CallbackQuery):
    split_data = callback.data.split(',')

    index = int(split_data[1])

    delete_index = divmod(index, 2)

    row = delete_index[0]
    column = delete_index[1]

    if column == 1:
        row = round(delete_index[0])

    return callback.message.reply_markup.inline_keyboard[row][column].text


async def showUserData(data: dict, from_call: str):
    enabled = None

    if from_call == "user":
        if data["enabled"] == 'N':
            enabled = "🔕Рассылка отключена🔕"
        else:
            enabled = "🔔Рассылка включена🔔"

    user_list = "<b>Информация об пользователе:</b>\n" \
                f"Имя пользователя: <b>{data['user_name']}</b>\n" \
                f"Ссылка на пользователя: <b>{data['user_link']}</b>\n" \

    if isinstance(enabled, str):
        user_list += f"Рассылка: <b>{enabled}</b>\n"

    if "rate_count" in data and "rate_score" in data:
        if from_call == "user":
            user_list += f"Рейтинг: <b>{data['rate_count']}</b>\n"\
                         f"Количество оценок: <b>{data['rate_score']}</b>"
        else:

            user_list += f"<b>Рейтинг: {data['rate_score']}\n"\
                         f"Количество оценок: {data['rate_count']}"\
                         f"\nПредлагаемая цена: {data['price']}</b>"

    return user_list


async def showRateData(state: FSMContext):
    data = await state.get_data()

    user_list = "<b>Информация об оценке пользователя:</b>\n" \
                f"Имя пользователя: <b>{data['user_link']}</b>\n" \
                f"Оценка: <b>{data['rate']}</b>\n" \
                f"Отзыв: <b>{data['review']}</b>\n"

    return user_list


async def prepareForShow(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    split_data = callback.data.split(',')

    try:
        data["is_forward"] = bool(int(split_data[1]))

        data["is_first"] = bool(int(split_data[2]))
    except IndexError:
        data["is_forward"] = False

    await state.set_data(data)


async def createOrderList(order_data: dict, is_full: bool, with_number: bool):
    order_list = f"<b>Информация об заказе:</b>\n"
    if with_number:
        order_list += f"-Номер заказа:<b>\t{order_data['id']}</b>\n"

    order_list += f"-Название предмета:<b>\n\t{order_data['subject'].title()}\n</b>" \
                  f"-Тип задания:<b>\n\t{order_data['work_type']}\n</b>" \
                  f"-Категория:<b>\n\t{order_data['category']}\n</b>" \
                  f"-Цена:<b>\t{str(order_data['price'])}\n</b>"
    if is_full:
        order_list += f"-Описание:<b>\n\t{order_data['order_condition']}\n</b>"

    return order_list


async def create_respond_list(respond_data: dict, is_full: bool):
    order_list = f"<b>Информация об отклике:</b>\n"\
                 f"-Номер заказа:<b>\t{respond_data['id']}</b>\n"\
                 f"-Название предмета:<b>\n\t{respond_data['subject'].title()}\n</b>" \
                 f"-Тип задания:<b>\n\t{respond_data['work_type']}\n</b>" \
                 f"-Категория:<b>\n\t{respond_data['category']}\n</b>" \
                 f"-Цена:<b>\t{str(respond_data['price'])}\n</b>"

    if is_full:
        order_list += f"-Предложенная цена:<b>\t{str(respond_data['respond_price'])}\n</b>"\
                      f"-Описание:<b>\n\t{respond_data['order_condition']}\n</b>"

    return order_list


async def createMediaList(data: list):
    send_photo_list = []

    if data:
        send_photo_text = "<b>Фотографии к заказу:</b>"

        for index, message in enumerate(data):
            if len(send_photo_list) < 10:
                send_photo_list.append(InputMediaPhoto(media=message.photo[-3].file_id))

        if send_photo_list:
            media = send_photo_list.pop(0).media
            send_photo_list.insert(0, InputMediaPhoto(media=media, caption=send_photo_text))

    return send_photo_list


async def createMediaMessages(order_data: dict):
    media = []

    if "photos" in order_data and order_data["photos"]:
        split_files = order_data["photos"].split(',')

        order_path = await generalFunctions.createNewMainFolders(category=order_data["category"],
                                                                 order_id=order_data["id"])

        for file in split_files:
            file_path = await generalFunctions.getFilePath(order_path=order_path, order_id=order_data["id"], file=file)

            file = FSInputFile(file_path)

            media.append(aiogram.types.InputMediaPhoto(media=file))

        input_media = media.pop(0).media

        media.insert(0, aiogram.types.InputMediaPhoto(media=input_media, caption="<b>Фотографии к заказу:</b>"))

    return media


async def update_user_info(message: Message):
    user_data = {"id": message.chat.id, "user_name": message.chat.first_name, "user_link": f"@{message.chat.username}"}

    await generalFunctions.updateUserData(data=user_data)
