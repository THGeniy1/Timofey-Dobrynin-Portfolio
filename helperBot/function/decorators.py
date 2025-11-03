import logging

import asyncio

from typing import Union


def errorDecorator(func):
    async def main_function(data: Union[dict, list]):
        task = asyncio.create_task(func(data))
        try:
            await task

            if not task.result():
                return True
            else:
                return task.result()

        except Exception as e:
            logging.error(msg=f"{func.__name__} : {e}")
            task.cancel()

    return main_function
