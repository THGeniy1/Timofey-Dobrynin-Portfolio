import redis
import json
import logging
from django.conf import settings

from storage.mixins import PrivateGetMixin

logger = logging.getLogger(__name__)


class JsonService(PrivateGetMixin):
    CACHE_KEY = "jsons:{file_name}"
    CACHE_TTL = 3600

    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_json(self, file_name: str):
        cache_key = self.CACHE_KEY.format(file_name=file_name)

        try:
            jsons = self.redis_client.get(cache_key)
        except Exception as e:
            return {"error": str(e)}
        if jsons and isinstance(jsons, str) and jsons.strip():
            try:
                return json.loads(jsons)
            except Exception as e:
                return {"error": str(e)}

        try:
            path = f"jsons/{file_name}"
            json_data = self.download_file(path=path)
            if json_data and isinstance(json_data, str) and json_data.strip():
                parsed_data = json.loads(json_data)
                self.redis_client.setex(cache_key, self.CACHE_TTL, json.dumps(parsed_data))
                return parsed_data
        except Exception as e:
            return {"error": str(e)}

        return {"error": "Файл пуст или не найден"}

    def refresh_json(self, file_name: str):
        cache_key = self.CACHE_KEY.format(file_name=file_name)

        try:
            hints_data = self.download_file(path=f"jsons/{file_name}")
            if hints_data:
                parsed_data = json.loads(hints_data)
                self.redis_client.setex(cache_key, self.CACHE_TTL, json.dumps(parsed_data))
                logger.info(f"Кеш обновлен вручную: {file_name}")
                return {"status": "updated", "file": file_name}
        except Exception as e:
            return {"status": "error", "message": str(e)}

        return {"status": "error", "message": "Не удалось загрузить файл"}
