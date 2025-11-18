import os

import shutil

import logging

import asyncio

import aiomysql

import configparser

from typing import Union

from DataBase import objectStorage

from function import decorators

config = configparser.ConfigParser()

config.read(r'D:\pythonProject\helperBot\config.ini')

orders_path = config.get('DATA_BASE_PATH', 'orders_path')

db_password = config.get('DATA_BASE_CONFIGS', 'password')

db_name = config.get('DATA_BASE_CONFIGS', 'db_name')

db_user = config.get('DATA_BASE_CONFIGS', 'user')

db_port = config.get('DATA_BASE_CONFIGS', 'port')

db_config = {"host": 'localhost', "port": 3306, "user": 'User', "password": db_password, "db": db_name}

cities = []

universities = {}


async def deleteFolder(path: str, delay: int):
    await asyncio.sleep(delay)

    try:
        shutil.rmtree(path=path)
    except FileNotFoundError:
        pass


async def getConnection():
    while True:
        try:
            cnx = await aiomysql.connect(**db_config, cursorclass=aiomysql.cursors.DictCursor)

            return cnx
        except Exception as e:
            logging.critical(msg=f"get_connection: {e}")
            continue


async def is_have_more(cursor: aiomysql.cursors.Cursor, query: str, value: list, len_result: int, is_forward: bool):
    is_more_taking = False

    if is_forward:
        value[-1] += len_result
    else:
        value[-1] -= len_result

    if value[-1] >= 0:
        await cursor.execute(query, tuple(value))

        result = await cursor.fetchall()

        if len(result) > 0:
            is_more_taking = True

    return is_more_taking


async def prepare_for_get(is_forward: bool, page_count: int, limit: int):
    if is_forward:
        page_count += 1
    else:
        page_count -= 1

    offset = (page_count - 1) * limit

    if offset < 0:
        page_count = 0
        offset = 0

    return offset, page_count


@decorators.errorDecorator
async def addNewUser(data: dict):
    db_connection = await getConnection()
    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                query = """CALL add_user(%s, %s, %s)"""

                values = (data["id"], data["user_name"], data["user_link"])

                await cursor.execute(query, values)

    except Exception as e:
        await db_connection.rollback()
        raise e


@decorators.errorDecorator
async def updateUserData(data: dict):
    db_connection = await getConnection()
    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                query = """CALL update_user_data(%s, %s, %s)"""

                values = (data["id"], data["user_name"], data["user_link"])
                await cursor.execute(query, values)

    except Exception as e:
        await db_connection.rollback()
        raise e


async def createNewMainFolders(category: str, order_id: Union[str, int]):
    if not os.path.exists(orders_path):
        os.mkdir(orders_path)

    category_path = orders_path + f"/{category}"
    if not os.path.exists(category_path):
        os.mkdir(category_path)

    order_path = f"{category_path}/{order_id}"

    if not os.path.exists(order_path):
        os.mkdir(order_path)
        asyncio.create_task(deleteFolder(path=order_path, delay=900))

    return order_path


async def getFilePath(order_path: str, order_id: Union[str, int], file: str):
    file_path = f"{order_path}/{file}"

    if not os.path.exists(file_path):
        await objectStorage.get_object(file_path=file_path, file_name=file, bucket_name=str(order_id))

    return file_path


async def checkInUserList(data: int):
    db_connection = await getConnection()

    async with db_connection:
        async with db_connection.cursor() as cursor:
            logging.info(msg=f"Date for user verification: {data}")

            query = """CALL check_in_user_list(%s)"""

            await cursor.execute(query, (data,))

            result = await cursor.fetchone()

            return bool(result)


async def checkInBlockedList(data: Union[int, str]):
    db_connection = await getConnection()

    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = """CALL check_in_blocked_list(%s)"""

            await cursor.execute(query, (data,))

            result = await cursor.fetchone()

            return bool(result)


async def getUser(user_id: Union[int, None], user_name: Union[str, None], cursor: Union[aiomysql.cursors.Cursor, None]):
    async def function():
        query = """CALL get_user(%s, %s)"""

        await cursor.execute(query, (user_id, user_name))

        return await cursor.fetchone()

    if cursor is None:
        db_connection = await getConnection()
        async with db_connection:
            async with db_connection.cursor() as cursor:
                return await function()
    else:
        return await function()


async def getCountUsers():
    db_connection = await getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = """CALL get_count_users()"""

            await cursor.execute(query)

            return (await cursor.fetchone())['COUNT(*)']


async def getCountOrders():
    db_connection = await getConnection()

    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = """CALL get_count_orders()"""

            await cursor.execute(query)

            return await cursor.fetchone()


@decorators.errorDecorator
async def getOrder(data: dict):
    db_connection = await getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:

            query = """CALL get_order_values(%s)"""

            await cursor.execute(query, (data["id"],))
            return await cursor.fetchone()


@decorators.errorDecorator
async def banUser(data: dict):
    db_connection = await getConnection()
    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                user_data = await getUser(user_id=None, user_name=data["user"], cursor=cursor)

                query = """CALL ban_user(%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                values = (user_data["id"], user_data["user_name"], user_data["city"], user_data["university"],
                          user_data["enabled"], user_data["rate_table"], user_data["user_table"],
                          user_data["orders_table"], data["reason"])

                await cursor.execute(query, values)

    except Exception as e:
        await db_connection.rollback()
        raise e


async def getALLUsers():
    db_connection = await getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:

            query = """CALL get_all_users()"""

            await cursor.execute(query)
            return await cursor.fetchall()


async def get_old_orders():
    db_connection = await getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:

            query = """CALL get_old_orders()"""

            await cursor.execute(query)
            return await cursor.fetchall()


async def get_respond_orders():
    db_connection = await getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:

            query = """CALL get_respond_orders()"""

            await cursor.execute(query)

            return await cursor.fetchall()


@decorators.errorDecorator
async def end_all_actions(data: dict):
    db_connection = await getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:

            query = """CALL end_all_user_actions(%s)"""

            await cursor.execute(query, (data["id"]))
