import logging
import django
from urllib.parse import parse_qs
from channels.db import database_sync_to_async

django.setup()

from rest_framework_simplejwt.tokens import AccessToken
from authentication.models import CustomUser

logger = logging.getLogger("django")


class JWTAuthMiddleware:

    def __init__(self, inner):
        self.inner = inner
        logger.info("MyMiddleware initialized")

    async def __call__(self, scope, receive, send):
        logger.info("MyMiddleware CALL")
        logger.info(f"Scope: {scope}")
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        token = query_params.get("token", [None])[0]

        if token:
            scope["user"] = await self.get_user(token)
            logger.info(f"WS Authenticated User: {scope['user']}")

            return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        try:
            access_token = AccessToken(token)
            return CustomUser.objects.get(id=access_token["user_id"])
        except Exception as e:
            logger.warning(f"Invalid token: {e}")
