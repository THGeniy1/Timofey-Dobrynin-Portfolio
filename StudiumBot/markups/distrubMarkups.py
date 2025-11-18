from typing import Union

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.utils.keyboard import InlineKeyboardBuilder

from Other import Texts


async def check_subscribe_markup():
    button1 = InlineKeyboardButton(text="Начать", callback_data='/start')

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1]])

    return markup


async def create_user_markup():
    button1 = InlineKeyboardButton(text="🔨Отклики🔨", callback_data='/responses')
    button2 = InlineKeyboardButton(text="⚙Заказы⚙", callback_data='/orders')
    button3 = InlineKeyboardButton(text="🌟Отзывы🌟", callback_data=f'/rating')
    button4 = InlineKeyboardButton(text="✉Рассылка✉", callback_data='/malling')

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1], [button2], [button3], [button4]])

    return markup


async def create_mover_markup(is_text: bool, index: int):
    movers = Texts.mover_list[index]

    buttons_list = []

    button1 = InlineKeyboardButton(text="⏪Вернуться", callback_data=movers[1])
    button2 = InlineKeyboardButton(text="Продолжить⏩", callback_data=movers[0])
    buttons_list.append([button1, button2])

    if is_text:
        button3 = InlineKeyboardButton(text="♻Отменить ввод♻", callback_data=movers[2])
        buttons_list.append([button3])
    else:
        if len(movers) == 4:
            button3 = InlineKeyboardButton(text="🗑️Удалить🗑️", callback_data=movers[-1])
            buttons_list.append([button3])

    markup = InlineKeyboardMarkup(inline_keyboard=buttons_list)

    return markup


async def create_corrected_markup(is_text: bool, index: int):
    movers = Texts.mover_list[index]

    buttons_list = []

    button1 = InlineKeyboardButton(text="👌🏻Исправлена👌🏻", callback_data=movers[0])
    buttons_list.append([button1])

    if is_text:
        button2 = InlineKeyboardButton(text="♻Отменить ввод♻", callback_data=movers[2])
        buttons_list.append([button2])
    else:
        if len(movers) == 4:
            button2 = InlineKeyboardButton(text="🗑️Удалить🗑️", callback_data=movers[-1])
            buttons_list.append([button2])

    markup = InlineKeyboardMarkup(inline_keyboard=buttons_list)

    return markup


async def create_is_executor_register():
    button1 = InlineKeyboardButton(text="🔔Да", callback_data='/receive,Y')
    button2 = InlineKeyboardButton(text="🔕Нет", callback_data='/receive,N')

    markup = InlineKeyboardMarkup(inline_keyboard=[[button2, button1]])

    return markup


async def create_is_correct_markup(index: int):
    corrects = Texts.is_correct_command[index]

    button1 = InlineKeyboardButton(text="👌🏻Верна👌🏻", callback_data=corrects[0])
    button2 = InlineKeyboardButton(text="🖊️Исправить🖊️", callback_data=corrects[1])

    markup = InlineKeyboardMarkup(inline_keyboard=[[button2, button1]])

    return markup


async def create_types_tuple(categories: Union[str, list]):
    types = []
    all_types = tuple(Texts.types_list.keys())

    if isinstance(categories, str):
        indexes = Texts.science_dict[categories]
    else:
        indexes = []
        for category in categories:
            for cat_indexes in Texts.science_dict[category]:
                if cat_indexes not in indexes:
                    indexes.append(cat_indexes)

    for index in sorted(indexes):
        types.append(all_types[index])

    return types


async def create_types_markup(start_index: int, categories: Union[str, list], is_forward: bool, mover_index: int):
    len_work_types = 5

    builder = InlineKeyboardBuilder()

    types = await create_types_tuple(categories=categories)
    mover = Texts.types_movers[mover_index]

    len_types = len(types)

    if is_forward:
        second_index = start_index + len_work_types
    else:
        second_index = start_index - len_work_types

    if abs(second_index) > len_types:
        second_index = len_types

    values = types[min(second_index, start_index):max(second_index, start_index)]

    for ind, work in enumerate(values):
        builder.button(text=work, callback_data=f"{mover[0]},{ind}")
        if ind == len(values) - 1:
            builder.adjust(2, 2)
            button_list = []

            if start_index > 0 < second_index <= len_types:
                button1 = InlineKeyboardButton(text="⬅Назад",
                                               callback_data=f"{mover[1]},0,{min(second_index, start_index)}")
                button_list.append(button1)

            if start_index >= 0 <= second_index < len_types:
                button2 = InlineKeyboardButton(text="Вперед➡",
                                               callback_data=f"{mover[1]},1,{max(second_index, start_index)}")
                button_list.append(button2)

            builder.row(*button_list, width=2)
            break

    return builder


async def create_science_markup(start_index: int, is_forward: bool, mover_index: int):
    len_sciences = 5

    builder = InlineKeyboardBuilder()

    categories = tuple(Texts.science_dict.keys())
    len_categories = len(categories)

    mover = Texts.science_movers[mover_index]

    second_index = len_sciences * (start_index + 1)

    if abs(second_index) > len_categories:
        if is_forward:
            second_index = len_categories
        else:
            second_index = 0

    values = categories[min(second_index, start_index):max(second_index, start_index)]

    for ind, science in enumerate(values):
        builder.button(text=science.title(), callback_data=f"{mover[0]}, {ind}")
        if ind == len(values) - 1:
            builder.adjust(2, 2)
            button_list = []

            if second_index >= len_categories:
                button1 = InlineKeyboardButton(text="⬅Назад",
                                               callback_data=f"{mover[1]},0,{min(second_index, start_index)}")
                button_list.append(button1)

            if start_index <= 1 or second_index == 0:
                button2 = InlineKeyboardButton(text="Вперед➡",
                                               callback_data=f"{mover[1]},1,{max(second_index, start_index)}")
                button_list.append(button2)

            builder.row(*button_list, width=2)
            break

    return builder


async def create_choose_fix_markup(index: int):
    builder = InlineKeyboardBuilder()
    values = Texts.global_correct_list[index]

    correct_values = values[0]
    command = values[-1]

    for ind, value in enumerate(correct_values):
        builder.button(text=value.title(), callback_data=f"{command}, {ind}")

    builder.adjust(2, 2)

    return builder


async def create_order_markup():
    button1 = InlineKeyboardButton(text="👷Просмотр откликов👷", callback_data=f'/show_tenders,1,1')

    button2 = InlineKeyboardButton(text="🔫Убрать с публикации🔫", callback_data='/end_order')

    button3 = InlineKeyboardButton(text="🖊Изменить данные🖊", callback_data='/orderNotCorrect')

    button4 = InlineKeyboardButton(text="⬆Вернуться⬆", callback_data='/orders_back')

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1], [button2], [button3], [button4]])

    return markup


async def create_order_menu_markup():
    button1 = InlineKeyboardButton(text="⬆Вернуться⬆", callback_data="/show_order_menu")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1]])

    return markup


async def create_back_responds_markup():
    button1 = InlineKeyboardButton(text="⬆Вернуться⬆", callback_data="/responds_back")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1]])

    return markup


async def create_back_rate_markup(from_call: int):
    if from_call == 1:
        callback = "/order_rate_back"
    else:
        callback = "/rate_back"

    button1 = InlineKeyboardButton(text="⬆Вернуться⬆", callback_data=callback)

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1]])

    return markup


async def create_end_order_markup():
    button1 = InlineKeyboardButton(text="✅Да!", callback_data="/confirm_end")

    button2 = InlineKeyboardButton(text="❌Нет!", callback_data="/cancel_end")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button2, button1]])

    return markup


async def create_end_respond_markup(index: str):
    button1 = InlineKeyboardButton(text="✅Да", callback_data=f"/confirm_end_respond,{index}")

    button2 = InlineKeyboardButton(text="❌Нет", callback_data="/cancel_end_respond")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button2, button1]])

    return markup


async def create_is_rate_markup():
    button1 = InlineKeyboardButton(text="❤Да", callback_data='/isRate,1')
    button2 = InlineKeyboardButton(text="💔Нет", callback_data='/isRate,0')

    markup = InlineKeyboardMarkup(inline_keyboard=[[button2, button1]])

    return markup


async def create_is_correct_filter():
    button1 = InlineKeyboardButton(text="🔎Показать🔎", callback_data="/show_orders,1,1")
    button2 = InlineKeyboardButton(text="🖊️Исправить🖊️", callback_data="/change_filters")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button2, button1]])

    return markup


async def create_filters_markup():
    button1 = InlineKeyboardButton(text="🗓️По дате🗓️", callback_data="/filter,2")
    button2 = InlineKeyboardButton(text="💸По цене💸", callback_data="/filter,1")
    button3 = InlineKeyboardButton(text="🅰По имени🅰", callback_data="/filter,3")
    button4 = InlineKeyboardButton(text="🧩По умолчанию🧩", callback_data="/filter,0")

    button5 = InlineKeyboardButton(text="📍Изменить фильтры📍", callback_data="/change_filters")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1, button2], [button3, button4], [button5]])

    return markup


async def create_page_mover_markup(index: int, is_forward: bool, is_more_take: bool, is_first: bool):
    button_list = []

    if index == 0:
        callback_data = "/show_tenders"
    elif index == 1:
        callback_data = "/show_orders"
    elif index == 2:
        callback_data = "/show_rates"
    else:
        callback_data = "/show_responds"

    if (is_first and is_more_take) or (not is_forward and not is_more_take and not is_first):
        button1 = InlineKeyboardButton(text="Далее➡", callback_data=f"{callback_data},1,0")
        button_list.append(button1)

    elif is_forward and not is_more_take and not is_first:
        button2 = InlineKeyboardButton(text="⬅Назад", callback_data=f"{callback_data},0,0")
        button_list.append(button2)

    elif is_more_take and not is_first:
        button2 = InlineKeyboardButton(text="⬅Назад", callback_data=f"{callback_data},0,0")
        button1 = InlineKeyboardButton(text="Далее➡", callback_data=f"{callback_data},1,0")
        button_list.extend([button2, button1])

    if button_list:
        markup = InlineKeyboardMarkup(inline_keyboard=[button_list])

        return markup


async def create_orders_markup(orders: list, is_forward: bool, is_more_take: bool, is_first: bool):
    builder = InlineKeyboardBuilder()

    for order in orders:
        builder.button(text=f"№{order['id']}", callback_data=f"/order,{order['id']}")

    builder.adjust(2, 2)

    if (is_first and is_more_take) or (not is_forward and not is_more_take and not is_first):
        button1 = InlineKeyboardButton(text="Далее➡", callback_data="/user_orders,1")
        builder.row(button1, width=1)

    elif is_forward and not is_more_take and not is_first:
        button2 = InlineKeyboardButton(text="⬅Назад", callback_data="/user_orders,0")
        builder.row(button2, width=1)

    elif is_more_take and not is_first:
        button2 = InlineKeyboardButton(text="⬅Назад", callback_data="/user_orders,0")
        button1 = InlineKeyboardButton(text="Далее➡", callback_data="/user_orders,1")
        builder.row(button1, button2, width=1)

    button3 = InlineKeyboardButton(text="⬆Вернуться⬆", callback_data="/show_orders_back")
    builder.row(button3, width=1)

    return builder


async def create_show_order_markup(order_data: dict):
    button1 = InlineKeyboardButton(text="🔎Показать🔎", callback_data=f"/show_order,{order_data['id']}")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1]])

    return markup


async def create_show_respond_markup(index: int):
    button1 = InlineKeyboardButton(text="🔎Показать🔎", callback_data=f"/show_respond,{index}")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1]])

    return markup


async def create_show_review_markup(user_id: int):
    button1 = InlineKeyboardButton(text="🌟Отзывы🌟", callback_data=f'/rating,{user_id}')

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1]])

    return markup


async def create_respond_actions_markup(index: int):
    button1 = InlineKeyboardButton(text="⭕Отменить отклик⭕", callback_data=f"/respond_end,{index}")
    button2 = InlineKeyboardButton(text="⬆Вернуться⬆", callback_data="/respond_back")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])

    return markup


async def create_respond_markup():
    button1 = InlineKeyboardButton(text="🔊Откликнутся🔊", callback_data=f"/respond")
    button2 = InlineKeyboardButton(text="⬆Вернуться⬆", callback_data="/return_show")

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])

    return markup


async def create_reg_respond_markup():
    movers = Texts.mover_list[1]

    button1 = InlineKeyboardButton(text="💥Создать отклик💥", callback_data=movers[0])

    button2 = InlineKeyboardButton(text="♻Отменить ввод♻", callback_data=movers[2])

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1], [button2]])

    return markup


async def create_back_after_actions_markup(index: int):
    if index == 0:
        callback = "/respond_back"
    else:
        callback = "/orders_back"

    button1 = InlineKeyboardButton(text="⬆Вернуться⬆", callback_data=callback)

    markup = InlineKeyboardMarkup(inline_keyboard=[[button1]])

    return markup
