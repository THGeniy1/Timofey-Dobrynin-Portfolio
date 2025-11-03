import re
import json
import logging
import base64
import hashlib
import requests
from typing import Dict, List, Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Staff

logger = logging.getLogger(__name__)

SELECTEL_TOKEN_URL = "https://cloud.api.selcloud.ru/identity/v3/auth/tokens"


def _build_token_payload() -> Dict:
    return {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "name": settings.SELECTEL_SERVICE_USER_USERNAME,
                        "domain": {"name": settings.SELECTEL_ACCOUNT_ID},
                        "password": settings.SELECTEL_SERVICE_USER_PASSWORD,
                    }
                }
            },
            "scope": {
                "project": {
                    "name": settings.SELECTEL_PROJECT_NAME,
                    "domain": {"name": settings.SELECTEL_ACCOUNT_ID},
                }
            }
        }
    }


def _make_selectel_token_request() -> str:
    payload = _build_token_payload()
    headers = {"Content-Type": "application/json"}

    resp = requests.post(SELECTEL_TOKEN_URL, headers=headers, data=json.dumps(payload), timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Failed to obtain Selectel token: {resp.status_code} {resp.text}")

    token = resp.headers.get("X-Subject-Token")
    if not token:
        raise RuntimeError("Missing Selectel token in response headers")
    return token


def _make_selectel_secrets_request(token: str) -> List[Dict]:
    url = "https://cloud.api.selcloud.ru/secrets-manager/v1/?list="
    headers = {"X-Auth-Token": token}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data.get("keys", [])


def _fetch_and_decode_secret(name: str) -> Dict[str, Any] | None:
    token = _make_selectel_token_request()
    url = f"https://cloud.api.selcloud.ru/secrets-manager/v1/{name}"
    headers = {"X-Auth-Token": token}

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    secret_data = resp.json()

    version_data = secret_data.get("version", {})
    if "value" not in version_data:
        return None

    try:
        decoded = base64.b64decode(version_data["value"]).decode("utf-8")
    except Exception as e:
        logger.error("Failed to decode secret %s: %s", name, e)
        return None

    parsed = {}
    status_match = re.search(r"Status:\s*(\S+)", decoded, re.IGNORECASE)
    name_match = re.search(r"name:\s*(.+)", decoded, re.IGNORECASE)
    login_match = re.search(r"Login:\s*(\S+)", decoded, re.IGNORECASE)
    password_match = re.search(r"(?:Passwrod|Password):\s*(\S+)", decoded, re.IGNORECASE)

    if status_match:
        parsed["status"] = status_match.group(1).strip()
    if name_match:
        parsed["name"] = name_match.group(1).strip()
    if login_match:
        parsed["email"] = login_match.group(1).strip()
    if password_match:
        parsed["password"] = password_match.group(1).strip()
    print("parsed", parsed)
    return parsed


def _normalize_admin_entries(raw_entries: List[Dict]) -> List[Dict]:
    normalized = []
    for entry in raw_entries:
        name = entry.get("name", "")
        if not name.startswith("admin_"):
            continue

        entry_data = _fetch_and_decode_secret(name)
        if not entry_data or not entry_data.get("email"):
            continue

        normalized.append(entry_data)

    normalized.sort(key=lambda x: (x.get("status", ""), x.get("email", "")))
    return normalized


@transaction.atomic
def sync_selectel_admins() -> Dict[str, int]:
    logger.info("Starting Selectel admin synchronization")

    token = _make_selectel_token_request()
    raw_entries = _make_selectel_secrets_request(token)
    admins = _normalize_admin_entries(raw_entries)

    User = get_user_model()
    remote_by_email = {a["email"].lower(): a for a in admins}
    remote_emails = set(remote_by_email.keys())

    existing_staff = Staff.objects.select_related("user").all()

    deleted = 0
    for staff in existing_staff:
        if staff.user and staff.user.email.lower() not in remote_emails:
            logger.info("Deleting staff for %s", staff.user.email)
            staff.delete()
            deleted += 1

    created = 0
    updated = 0
    for email, info in remote_by_email.items():
        user, created_user = User.objects.get_or_create(
            email=email,
            defaults={
                "name": info.get("name", ""),
                "is_active": True,
                "is_staff": True,
                "is_superuser": info.get("status") == "superadmin",
            }
        )

        changed = False

        if user.name != info.get("name", ""):
            user.name = info.get("name", "")
            changed = True

        is_super = info.get("status") == "superadmin"
        is_staff_flag = info.get("status") in ("superadmin", "moderator")
        if user.is_superuser != is_super:
            user.is_superuser = is_super
            changed = True
        if user.is_staff != is_staff_flag:
            user.is_staff = is_staff_flag
            changed = True

        password = info.get("password", "").strip()
        if password and not user.check_password(password):
            print("СТАВИМ ПАРОЛЬ", password)
            user.set_password(password)
            changed = True

        if changed:
            user.save(update_fields=["name", "is_staff", "is_superuser", "password"])

        staff, created_staff = Staff.objects.get_or_create(
            user=user,
            defaults={"role": info.get("status")}
        )
        if not created_staff and staff.role != info.get("status"):
            staff.role = info.get("status")
            staff.save(update_fields=["role"])

        if created_user or created_staff:
            created += 1
        else:
            updated += 1

    result = {"created": created, "updated": updated, "deleted": deleted}
    logger.info("Selectel admin synchronization completed: %s", result)
    return result

    
def _build_fernet_key_from_secret() -> bytes:
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_text(plain_text: str) -> str:
    if plain_text is None:
        return ""
    plain_text = str(plain_text)
    if plain_text == "":
        return ""
    from cryptography.fernet import Fernet
    f = Fernet(_build_fernet_key_from_secret())
    token = f.encrypt(plain_text.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: str) -> str:
    if not token:
        return ""
    try:
        from cryptography.fernet import Fernet
        f = Fernet(_build_fernet_key_from_secret())
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""

