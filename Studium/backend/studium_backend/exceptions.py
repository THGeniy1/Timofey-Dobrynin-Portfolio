from rest_framework import status


class AppException(Exception):
    default_status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Ошибка при выполнении запроса"

    def __init__(self, message=None, status_code=None, code=None):
        self.message = message or self.default_message
        self.status_code = status_code or self.default_status_code
        self.code = code or self.__class__.__name__
        super().__init__(self.message)