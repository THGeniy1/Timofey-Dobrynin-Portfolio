import asyncio

import main

from function import decorators

from DataBase import generalFunctions

len_orders = 4


async def create_search_string(objects: list):
    new_objects = []

    for obj in objects:
        split_obj = obj.split()

        if len(split_obj) > 1:
            obj = f"+{split_obj[0]} -{split_obj[1]}"

        new_objects.append(obj)

    search_string = ', '.join(f'"{item}"' for item in new_objects)

    return search_string


async def prepare_for_taking(data: dict):
    search_objects = ["work_types", "categories", "subjects"]
    simple_objects = ["work_type", "category", "subject"]

    filters_values = data["filter"].split(',')
    order_by_options = ["id", "price", "create_date", "subject"]
    order_by = order_by_options[int(filters_values[0]) % len(order_by_options)]

    order_direction = "DESC"

    if filters_values[1] == "1":
        if int(filters_values[0]) != (2 and 0):
            order_direction = "ASC"

    offset, page_count = await generalFunctions.prepare_for_get(is_forward=data["is_forward"],
                                                                page_count=data["page_count"],
                                                                limit=len_orders)

    main_query = """SELECT id, price, subject, work_type, category, create_date FROM orders\t"""

    for index, search_object in enumerate(search_objects):
        if search_object in data and data[search_object]:
            if search_object == "work_types":
                search_string = await create_search_string(objects=data[search_object])
            else:
                search_string = ', '.join(f'"{item}"' for item in data[search_object])

            if "WHERE" in main_query:
                main_query += "AND "
            else:
                main_query += "WHERE "

            main_query += f"MATCH ({simple_objects[index]}) AGAINST ('{search_string}' IN BOOLEAN MODE) "

    if "WHERE" in main_query:
        main_query += "AND "
    else:
        main_query += "WHERE "

    main_query += f"active = 'Y' ORDER BY {order_by} {order_direction} LIMIT ? OFFSET ?"

    return main_query, page_count, offset


@decorators.errorDecorator
async def getOrders(data: dict):
    main_query, page_count, offset = await prepare_for_taking(data=data)

    results = {"orders": [], "page_count": page_count}

    db_connection = await generalFunctions.getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = "CALL get_orders(%s, %s, %s)"

            values = [main_query, len_orders, offset]

            await cursor.execute(query, tuple(values))

            results["orders"] = await cursor.fetchall()

            results["is_more_take"] = await generalFunctions.is_have_more(cursor=cursor,
                                                                          query=query,
                                                                          value=values,
                                                                          len_result=len(results["orders"]),
                                                                          is_forward=data["is_forward"])

    return results


@decorators.errorDecorator
async def add_respond(data: list):
    db_connection = await generalFunctions.getConnection()

    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                query = """CALL add_response(%s, %s, %s)"""

                values = (data[0], data[1], data[2])

                await cursor.execute(query, values)

                result = await cursor.fetchone()

        if result:
            asyncio.create_task(main.call_user(order_id=data[0], user_id=data[1]))

        return result

    except Exception as e:
        await db_connection.rollback()
        raise e


@decorators.errorDecorator
async def get_user_responds(data: dict):
    limit = 4

    offset, page_count = await generalFunctions.prepare_for_get(is_forward=data["is_forward"],
                                                                page_count=data["page_responds"],
                                                                limit=limit)

    db_connection = await generalFunctions.getConnection()
    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = """CALL get_user_responses(%s, %s, %s)"""

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
                    order_data = await generalFunctions.getOrder(data={"id": result["order_id"]})

                    results[index] = order_data
                    results[index]["respond_price"] = result["price"]

            else:
                page_count = None

            result = {"responds": results, "page_responds": page_count, "is_more_take": is_more_take}

            return result


@decorators.errorDecorator
async def get_responds_counts(data: dict):
    db_connection = await generalFunctions.getConnection()

    async with db_connection:
        async with db_connection.cursor() as cursor:
            query = """CALL get_responses_counts(%s)"""

            values = (data["id"],)

            await cursor.execute(query, values)

            result = await cursor.fetchone()

            return result


@decorators.errorDecorator
async def end_respond(data: dict):
    db_connection = await generalFunctions.getConnection()

    try:
        async with db_connection:
            async with db_connection.cursor() as cursor:
                query = """CALL end_respond(%s, %s)"""

                values = (data['order_id'], data['user_id'])

                await cursor.execute(query, values)

    except Exception as e:
        await db_connection.rollback()
        raise e
