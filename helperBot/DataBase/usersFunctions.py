import main

import asyncio

from typing import Union

from function import decorators

from DataBase import generalFunctions


async def spaces_in_underlining(text: str):
    value = text.split()
    if len(value) > 1:
        text = '_'.join(value)
    return text


@decorators.errorDecorator
async def changeStateMalling(data: dict):
    db_connection = await generalFunctions.getConnection()
    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                query = """CALL change_malling_state(%s, %s)"""
                values = (data["id"], data["enabled"])

                await cursor.execute(query, values)

    except Exception as e:
        await db_connection.rollback()
        raise e


async def create_photo_string(data: dict):
    corus = []

    for message in data["photos"]:
        corus.append(main.get_file_name(message=message))

    flies = await asyncio.gather(*corus)

    files_string = ",".join(flies)

    return files_string


async def load_photos(data: dict, order_id: Union[str, int]):
    corus = []

    order_path = await generalFunctions.createNewMainFolders(category=data["category"], order_id=order_id)

    for file in data["photos"]:
        corus.append(main.downloader(message=file, order_id=order_id, insert_path=order_path))

    await asyncio.gather(*corus)


@decorators.errorDecorator
async def add_order(data: dict):
    db_connection = await generalFunctions.getConnection()

    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                files_string = ""

                if "photos" in data and data["photos"]:
                    files_string = await create_photo_string(data=data)

                query = """CALL add_order(%s, %s, %s, %s, %s, %s, %s)"""

                values = (data['user_id'], data["price"], data["subject"], data["work_type"],
                          data["category"], data["order_condition"], files_string)

                await cursor.execute(query, values)

                order_id = (await cursor.fetchone())["order_id"]

                await load_photos(data=data, order_id=order_id)

                await cursor.execute("""CALL get_active_users()""")

                active_users = await cursor.fetchall()

                await main.notifications_active(users=active_users)

                return order_id

    except Exception as e:
        await db_connection.rollback()
        raise e


@decorators.errorDecorator
async def update_order(data: dict):
    db_connection = await generalFunctions.getConnection()

    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                files_string = ""

                if "photos" in data and data["photos"]:
                    files_string = await create_photo_string(data=data)

                    await load_photos(data=data, order_id=data["id"])

                query = """CALL update_order_data(%s, %s, %s, %s, %s, %s, %s)"""

                values = (data["id"], data["price"], data["subject"], data["work_type"],
                          data["category"], data["order_condition"], files_string)

                await cursor.execute(query, values)

    except Exception as e:
        await db_connection.rollback()
        raise e


@decorators.errorDecorator
async def end_order(data: dict):
    db_connection = await generalFunctions.getConnection()

    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                query = """CALL end_order(%s)"""

                values = (data["id"])

                await cursor.execute(query, values)

    except Exception as e:
        await db_connection.rollback()
        raise e


@decorators.errorDecorator
async def get_user_orders(data: dict):
    limit = 4

    offset, page_count = await generalFunctions.prepare_for_get(is_forward=data["is_forward"],
                                                                page_count=data["page_orders"],
                                                                limit=limit)

    db_connection = await generalFunctions.getConnection()

    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = """CALL get_user_orders(%s, %s, %s)"""

            values = [data['user_data']['id'], limit, offset]

            await cursor.execute(query, tuple(values))

            results = await cursor.fetchall()

            is_more_take = await generalFunctions.is_have_more(cursor=cursor, query=query, value=values,
                                                               len_result=len(results), is_forward=data["is_forward"])

            if not results:
                page_count = None

            result = {"orders": results, "page_orders": page_count, "is_more_take": is_more_take}

            return result


@decorators.errorDecorator
async def get_order_tenders(data: dict):
    executors = []
    limit = 6

    offset, page_count = await generalFunctions.prepare_for_get(is_forward=data["is_forward"],
                                                                page_count=data["page_tenders"],
                                                                limit=limit)

    db_connection = await generalFunctions.getConnection()

    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = """CALL get_tenders(%s, %s, %s)"""

            values = [data["order_data"]["id"], limit, offset]

            await cursor.execute(query, tuple(values))

            results = await cursor.fetchall()

            is_more_take = await generalFunctions.is_have_more(cursor=cursor, query=query, value=values,
                                                               len_result=len(results), is_forward=data["is_forward"])

            if results:
                for executor in results:
                    data = await generalFunctions.getUser(user_id=executor['user_id'], user_name=None, cursor=cursor)

                    if data:
                        data['price'] = executor['price']

                        executors.append(data)

            return {"executors": executors, "page_tenders": page_count, "is_more_take": is_more_take}


@decorators.errorDecorator
async def rate_user(data: dict):
    db_connection = await generalFunctions.getConnection()
    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                user_data = await generalFunctions.getUser(user_id=None, user_name=data['user_link'], cursor=cursor)

                if user_data and data["rated_user"] != user_data["id"]:

                    query = """CALL rate_user(%s, %s, %s, %s, %s)"""

                    values = (data["order_id"], user_data["id"], data["rate_user"], data["rate"], data["review"])

                    await cursor.execute(query, values)

                else:
                    raise Exception("Совпали ID")

    except Exception as e:
        await db_connection.rollback()
        raise e


@decorators.errorDecorator
async def get_user_rate(data: dict):
    limit = 6

    offset, page_count = await generalFunctions.prepare_for_get(is_forward=data["is_forward"],
                                                                page_count=data["page_rating"],
                                                                limit=limit)

    db_connection = await generalFunctions.getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = """CALL get_user_rate(%s, %s, %s)"""

            values = [data["user_data"]["id"], limit, offset]

            await cursor.execute(query, tuple(values))

            results = await cursor.fetchall()

            is_more_take = await generalFunctions.is_have_more(cursor=cursor,
                                                               query=query,
                                                               value=values,
                                                               len_result=len(results),
                                                               is_forward=data["is_forward"])
            if results:
                for index, result in enumerate(results):
                    user_data = await generalFunctions.getUser(user_id=result["rate_id"],
                                                               user_name=None,
                                                               cursor=cursor)

                    results[index]["rated_user_link"] = user_data["user_link"]
                    results[index]["rated_user_name"] = user_data["user_name"]

            else:
                page_count = None

            result = {"rates": results, "page_rating": page_count, "is_more_take": is_more_take}

            return result
