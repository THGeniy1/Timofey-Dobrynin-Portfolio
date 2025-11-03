import hashlib
import requests
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.conf import settings
from authentication.utils import decrypt_text

logger = logging.getLogger(__name__)


class TinkoffAPI:
    VALIDATION_FIELDS = {
        'AUTHORIZED': {'TerminalKey', 'OrderId', 'Success', 'Status', 'PaymentId', 'ErrorCode', 'Amount'},
        'CONFIRMED': {'TerminalKey', 'OrderId', 'Success', 'Status', 'PaymentId', 'ErrorCode', 'Amount'},
        'REJECTED': {'TerminalKey', 'OrderId', 'Success', 'Status', 'PaymentId', 'ErrorCode'},
        'CANCELED': {'TerminalKey', 'OrderId', 'Success', 'Status', 'PaymentId', 'ErrorCode'},
        'REFUNDED': {'TerminalKey', 'OrderId', 'Success', 'Status', 'PaymentId', 'ErrorCode', 'Amount'},
        'REVERSED': {'TerminalKey', 'OrderId', 'Success', 'Status', 'PaymentId', 'ErrorCode'},
        'RECURRING': {'TerminalKey', 'OrderId', 'Success', 'Status', 'PaymentId', 'ErrorCode', 'Amount', 'RebillId'},
    }

    REMOVE_FIELDS = ['DATA', 'Receipt', 'NotificationURL', 'Token']

    REQUEST_FIELDS = {
        'Init': {'TerminalKey', 'Amount', 'OrderId'},
        'Cancel': {'TerminalKey', 'PaymentId'},
        'GetState': {'TerminalKey', 'PaymentId'},
        'Confirm': {'TerminalKey', 'PaymentId', 'Amount'},
        'Charge': {'TerminalKey', 'PaymentId', 'RebillId'},
        'AddCustomer': {'TerminalKey', 'CustomerKey'},
        'GetCustomer': {'TerminalKey', 'CustomerKey'},
        'RemoveCustomer': {'TerminalKey', 'CustomerKey'},
    }

    def generate_token(self, data: dict) -> str:
        exclude_fields_lower = [field.lower() for field in self.REQUEST_FIELDS]

        flat_data = {
            k.lower(): str(v) if v is not None else ''
            for k, v in data.items()
            if (not isinstance(v, (dict, list)) and
                k.lower() != "token" and
                k.lower() not in exclude_fields_lower)
        }
        flat_data["password"] = settings.TINKOFF_PASSWORD

        sorted_items = sorted(flat_data.items(), key=lambda x: x[0])

        concat_str = "".join(str(v) for _, v in sorted_items)

        return hashlib.sha256(concat_str.encode()).hexdigest()

    def generate_validation_token(self, data: dict) -> str:
        print(f"=== ГЕНЕРАЦИЯ ТОКЕНА ВАЛИДАЦИИ ===")
        print(f"Входные данные: {data}")

        filtered_data = {}
        for field in data:
            if field not in self.REMOVE_FIELDS:
                if field == "Success":
                    filtered_data[field] = str(data[field]).lower()
                else:
                    filtered_data[field] = str(data[field]) if data[field] is not None else ''
                print(f"Поле '{field}': '{data[field]}' -> '{filtered_data[field]}'")

        filtered_data["Password"] = settings.TINKOFF_PASSWORD
        print(f"Добавлен пароль: '{settings.TINKOFF_PASSWORD}'")

        sorted_items = sorted(filtered_data.items(), key=lambda x: x[0])
        print(f"Отсортированные данные: {sorted_items}")

        concat_str = "".join(str(v) for _, v in sorted_items)
        print(f"Строка для хеширования: '{concat_str}'")

        hash_result = hashlib.sha256(concat_str.encode()).hexdigest()
        print("=== ЗАВЕРШЕНИЕ ГЕНЕРАЦИИ ТОКЕНА ===\n")

        return hash_result

    def validate_token(self, data: dict) -> bool:
        try:
            received_token = data.get("Token") or data.get("token")
            if not received_token:
                logger.warning("Нет токена в данных для проверки")
                return False

            generated_token = self.generate_validation_token(data)

            print(f"Сгенерированный токен валидации: {generated_token}")
            print(f"Полученный токен: {received_token}")

            return received_token == generated_token

        except Exception as e:
            logger.error(f"Ошибка валидации токена: {e}")
            return False

    def request(self, endpoint: str, payload: dict) -> dict:
        payload["Token"] = self.generate_token(payload)

        url = f"{settings.TINKOFF_API_URL}/{endpoint}"

        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed request to {endpoint}: {e}")
            return {"Success": False, "Error": str(e)}

    def cancel_payment(self, payment_id: str) -> dict:
        payload = {
            "TerminalKey": settings.TINKOFF_TERMINAL_KEY,
            "PaymentId": payment_id
        }

        try:
            resp = requests.post(
                "https://securepay.tinkoff.ru/v2/Cancel",
                json={**payload, "Token": self.generate_token(payload)}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Cancel payment {payment_id} failed: {e}")
            return {"Success": False, "Error": str(e)}

    def confirm_payment(self, payment_id: str) -> dict:
        payload = {
            "TerminalKey": settings.TINKOFF_TERMINAL_KEY,
            "PaymentId": payment_id,
        }

        payload["Token"] = self.generate_token(payload)

        url = f"{settings.TINKOFF_API_URL}/Confirm"
        print("URL", url)
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            print("Ответ по подтверждению платежа", data)
            if not data.get("Success"):
                logger.warning(f"Подтверждение платежа не удалось: {data.get('ErrorMessage')}")
            return data

        except Exception as e:
            print("ОШИБКА ПРИ ПОДТВЕРЖДЕНИИ ПЛАТЕЖА", e)
            logger.error(f"Confirm payment {payment_id} failed: {e}")
            return {"Success": False, "Error": str(e)}

class AtolService:
    _instance: Optional["AtolService"] = None

    def __init__(self) -> None:
        self._base_url: str = getattr(settings, "ATOL_BASE_URL", "").rstrip("/")
        self._login: str = getattr(settings, "ATOL_LOGIN", "")
        self._password: str = getattr(settings, "ATOL_PASSWORD", "")
        self._group_code: str = getattr(settings, "ATOL_GROUP_CODE", "")
        self._payment_address: str = getattr(settings, "ATOL_PAYMENT_ADDRESS", "")

        self._payment_type: int = int(getattr(settings, "ATOL_PAYMENT_TYPE", 1))
        self._sno_default: str = getattr(settings, "ATOL_SNO", "usn_income_outcome")
        self._company_inn_default: str = getattr(settings, "ATOL_COMPANY_INN", "")
        self._company_email_default: Optional[str] = getattr(settings, "ATOL_COMPANY_EMAIL", None)
        self._agent_type_default: Optional[str] = getattr(settings, "ATOL_AGENT_TYPE", None)

        if not all([self._base_url, self._login, self._password, self._group_code, self._payment_address]):
            raise RuntimeError("ATOL settings не настроены полностью")

        self._token: Optional[str] = None
        self._session = requests.Session()

    @classmethod
    def instance(cls) -> "AtolService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_regular_receipt(
        self,
        external_id: str,
        total: float,
        items: List[Dict[str, Any]],
        client: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._create_sale_receipt(
            external_id=external_id,
            total=total,
            items=items,
            client=client,
            is_agent=False,
            operation="sell",
        )

    def create_agent_receipt(
            self,
            external_id: str,
            total: float,
            items: List[Dict[str, Any]],
            client: Optional[Dict[str, Any]] = None,
            supplier_user: Optional[Any] = None,
    ) -> Dict[str, Any]:
        if supplier_user and getattr(supplier_user, 'client', None) and supplier_user.client.is_admin_seller_account:
            is_agent = False
            supplier_user = None
        else:
            is_agent = True

        return self._create_sale_receipt(
            external_id=external_id,
            total=total,
            items=items,
            client=client,
            supplier_user=supplier_user,
            is_agent=is_agent,
            operation="sell",
        )

    def create_refund_receipt(
        self,
        external_id: str,
        total: float,
        items: List[Dict[str, Any]],
        client: Optional[Dict[str, Any]] = None,
        supplier_user=None,
    ) -> Dict[str, Any]:
        return self._create_sale_receipt(
            external_id=external_id,
            total=total,
            items=items,
            client=client,
            supplier_user=supplier_user,
            is_agent=True,
            operation="sell_refund",
        )

    def _create_sale_receipt(
        self,
        external_id: str,
        total: float,
        items: List[Dict[str, Any]],
        client: Optional[Dict[str, Any]] = None,
        supplier_user=None,
        is_agent: bool = False,
        operation: str = "sell",
    ) -> Dict[str, Any]:

        now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        company = {
            "inn": self._company_inn_default,
            "sno": self._sno_default,
            "payment_address": self._payment_address,
        }
        if self._company_email_default:
            company["email"] = self._company_email_default

        agent_info = None
        supplier_info = None

        if is_agent and supplier_user:
            is_foreign = getattr(supplier_user.client, "is_foreign_citizen", False)
            has_inn = getattr(supplier_user.client, "has_inn", False)

            if is_foreign == has_inn:
                raise ValueError("У пользователя должно быть либо is_foreign_citizen=True, либо has_inn=True")

            if is_foreign:
                supplier_inn = "000000000000"
            else:
                encrypted_inn = getattr(supplier_user.client, "inn", "")
                supplier_inn = decrypt_text(encrypted_inn)
                print("supplier_inn", supplier_inn)
                if not supplier_inn:
                    raise ValueError("Не удалось расшифровать ИНН поставщика")

            supplier_info = {"inn": supplier_inn}

            if self._agent_type_default:
                agent_info = {"type": self._agent_type_default}

        enriched_items = []
        for item in items:
            copy_item = dict(item)
            if agent_info:
                copy_item["agent_info"] = agent_info
            if supplier_info:
                copy_item["supplier_info"] = supplier_info
            enriched_items.append(copy_item)

        payload = {
            "timestamp": now_str,
            "external_id": str(external_id),
            "service": {"callback_url": f"{settings.BASE_URL}/api/payments/atol_callback/"},
            "receipt": {
                "client": client or {},
                "company": company,
                "items": enriched_items,
                "payments": [{"type": self._payment_type, "sum": float(total)}],
                "total": float(total),
            },
        }

        return self._post_with_retry(f"/{self._group_code}/{operation}", payload)

    def _post_with_retry(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._token:
            self._authenticate(force=True)
        url = f"{self._base_url}{path}"
        headers = self._headers()

        response = self._session.post(url, json=payload, headers=headers, timeout=20)
        data = response.json()

        if self._is_expired_token(response, data):
            self._authenticate(force=True)
            response = self._session.post(url, json=payload, headers=self._headers(), timeout=20)
            data = response.json()

        if response.status_code not in [200, 201, 202]:
            raise ValueError(f"Ошибка при формировании чека {response.status_code}! Информация: {data}")

        logger.debug("ATOL RESPONSE URL %s", url)
        logger.debug("ATOL RESPONSE payload %s", payload)
        logger.debug("ATOL RESPONSE headers %s", headers)
        logger.debug("ATOL RESPONSE data %s", data)
        return data

    def _authenticate(self, force: bool = False) -> None:
        if self._token and not force:
            return
        auth_url = f"{self._base_url}/getToken"
        try:
            resp = self._session.post(
                auth_url,
                json={"login": self._login, "pass": self._password},
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data and data['error'] is not None:
                raise RuntimeError(f"ATOL auth error: {data['error']}")
            self._token = data.get("token") or data.get("data", {}).get("token")
            if not self._token:
                raise RuntimeError("ATOL auth failed: token not received")
        except requests.RequestException as e:
            logger.error(f"ATOL authentication request failed: {e}")
            raise

    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json", "Token": self._token or ""}

    @staticmethod
    def _is_expired_token(response: requests.Response, data: Dict[str, Any]) -> bool:
        if response.status_code in (401, 403):
            return True
        error = data.get("error") or {}
        code = error.get("code") if isinstance(error, dict) else None
        if code == "ExpiredToken":
            return True
        text = error.get("text") if isinstance(error, dict) else None
        return bool(text and "expired" in str(text).lower())
