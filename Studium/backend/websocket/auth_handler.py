import asyncio
import logging
from datetime import datetime, timezone
from urllib.parse import parse_qs

from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger('auth_handler')


class AuthHandler:
    def __init__(self, consumer):
        self.consumer = consumer
        self.user_id = None
        self.token = None
        self.token_expire = None

    async def authenticate_user(self):
        self.token = self._get_token_from_scope()

        if not self.token:
            await self.consumer.close(code=4001)
            return False

        self.user_id, expiry_time = self._validate_token(self.token)
        if not self.user_id:
            await self.consumer.close(code=4001)
            return False

        self._start_token_expiry_timer(expiry_time)
        return True

    async def update_token(self, new_token):
        self.user_id, expiry_time = self._validate_token(new_token)
        if not self.user_id:
            await self.consumer.send_json({"error": "Неверный или истекший токен"})
            return False

        self.token = new_token
        if self.token_expiry_task:
            self.token_expiry_task.cancel()
        self._start_token_expiry_timer(expiry_time)
        await self.consumer.send_json({"status": "Токен обновлён"})
        return True

    def cleanup(self):
        if self.token_expiry_task:
            self.token_expiry_task.cancel()

    def _get_token_from_scope(self):
        query_string = self.consumer.scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        return query_params.get("token", [None])[0]

    @staticmethod
    def _validate_token(token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            exp_timestamp = access_token["exp"]
            expiry_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            remaining_time = (expiry_time - datetime.now(timezone.utc)).total_seconds()

            if remaining_time <= 0:
                return None, None
            return user_id, remaining_time + 10
        except Exception:
            return None, None

    def _start_token_expiry_timer(self, expiry_time):
        if expiry_time:
            self.token_expiry_task = asyncio.create_task(self._close_after_expiry(expiry_time))

    async def _close_after_expiry(self, timeout):
        await asyncio.sleep(timeout)
        await self.consumer.close(code=4002)
