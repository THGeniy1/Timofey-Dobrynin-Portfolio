from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from studium_backend.decorators import catch_and_log_exceptions
from .models import Rules
from .serializers import RulesSerializer

from collections import defaultdict
from storage.mixins import PublicGetMixin


class RulesListAPIView(APIView, PublicGetMixin):
    serializer_class = RulesSerializer
    permission_classes = (AllowAny,)

    @catch_and_log_exceptions
    def get(self, request):
        rules_qs = Rules.objects.all().order_by('-create_date')

        grouped_data = defaultdict(list)
        
        for rule in rules_qs:
            href = self.handle_get_file(rule.path)

            grouped_data[rule.type].append({
                "label": rule.name,
                "href": href,
                "date": rule.create_date,
            })

        result = []

        for rule_type, entries in grouped_data.items():
            result.append({
                "title": self.get_title(rule_type),
                "currentLink": entries[0]["href"] if entries else None,
                "previousLinks": [
                    {
                        "label": e["date"].strftime("%d.%m.%Y"),
                        "href": e["href"]
                    }
                    for e in entries[1:]
                ]
            })

        return Response(result, status=status.HTTP_200_OK)

    @staticmethod
    def get_title(type_key):
        return {
            "rules": "Правила пользователя",
            "offer": "Договор оферта",
            "privacy_politic": "Политика конфиденциальности",
        }.get(type_key, "Неизвестный раздел")
