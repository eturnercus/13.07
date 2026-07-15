"""Клиент ATEN CN8000 / CN8000A: логин и скачивание JNLP."""

from __future__ import annotations

import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Literal

from kvm_transport import DEFAULT_TIMEOUT, KvmHttpClient, KvmHttpError, parse_host


KvmType = Literal["old", "new"]


@dataclass
class SessionInfo:
    kvm_type: KvmType
    jnlp_url: str
    session_id: str | None = None
    str_url: str | None = None


class Cn8000Error(Exception):
    """Базовая ошибка клиента CN8000."""

    def __init__(self, code: str, **params: str) -> None:
        self.code = code
        self.params = params
        super().__init__(code)


class LoginError(Cn8000Error):
    """Ошибка авторизации или создания сессии."""


class JnlpError(Cn8000Error):
    """Не удалось получить JNLP-файл."""


def _map_transport_error(client: KvmHttpClient, exc: KvmHttpError) -> Cn8000Error:
    code = exc.code
    params = exc.params
    url = f"https://{client.hostname}{params.get('path', '')}"

    if code == "timeout":
        return Cn8000Error("error.timeout", seconds=params.get("seconds", str(int(client.timeout))))
    if code == "dns_timeout":
        return Cn8000Error("error.dns_timeout", host=params.get("host", client.hostname))
    if code == "dns_failed":
        return Cn8000Error("error.dns_failed", host=params.get("host", client.hostname))
    if code == "http_status":
        return Cn8000Error("error.http_status", url=url, status=params.get("status", "?"))
    return Cn8000Error("error.network", url=url, detail=params.get("detail", code))


def _request(
    client: KvmHttpClient,
    path: str,
    *,
    data: bytes | None = None,
    cookie: str | None = None,
    method: str = "GET",
) -> tuple[bytes, dict[str, str]]:
    try:
        return client.request(method, path, body=data, cookie=cookie)
    except KvmHttpError as exc:
        raise _map_transport_error(client, exc) from exc


def detect_kvm_type(client: KvmHttpClient) -> tuple[KvmType, str | None]:
    body, _ = _request(client, "/")
    text = body.decode("utf-8", errors="replace")
    match = re.search(r'strURL.*\+\s*"/(\w+?)"', text)
    if match:
        return "new", match.group(1)
    return "old", None


def _login_old(client: KvmHttpClient, username: str, password: str) -> str:
    ts = time.strftime("%Y.%m.%d.%H.%M.%S.") + f"{int(time.time() * 1000)}000.-180"
    form = urllib.parse.urlencode(
        {
            "username": username,
            "password": password,
            "login": "Login",
            "curtime": ts,
        }
    ).encode("ascii")
    body, _ = _request(client, "/view.htm", data=form, method="POST")
    text = body.decode("utf-8", errors="replace")
    match = re.search(r"global_sessionpid='(\w+?)'", text)
    if not match:
        raise LoginError("error.login.failed")
    return match.group(1)


def _login_new(
    client: KvmHttpClient,
    str_url: str,
    username: str,
    password: str,
    login_host: str,
) -> str:
    page_body, _ = _request(client, f"/{str_url}")
    page = page_body.decode("utf-8", errors="replace")
    tid_match = re.search(r'name="KVMIP_TARGETID" value="(\w+?)"', page)
    if not tid_match:
        raise LoginError("error.login.no_target")
    target_id = tid_match.group(1)

    login_value = f"{username}+{password}+{login_host}+{target_id}"
    form = (
        f"KVMIP_GMTIME={int(time.time())}"
        f"&KVMIP_DIFFTIME=420"
        f"&KVMIP_LOGIN={login_value}"
        f"&KVMIP_TARGETID={target_id}"
    ).encode("ascii")

    _, headers = _request(client, f"/{str_url}", data=form, method="POST")
    sid = KvmHttpClient.extract_sid(headers)
    if not sid:
        raise LoginError("error.login.failed")

    xid = f"0.{int(time.time() * 1_000_000) % 10**17:017d}"
    inquery_body = urllib.parse.urlencode(
        {
            "/Inquery?update": "31",
            "com_common": "01",
            "xid": xid,
            "SID": sid,
        }
    ).encode("ascii")
    _request(client, "/Inquery", data=inquery_body, cookie=f"sid={sid}", method="POST")
    return sid


def fetch_jnlp(
    host: str,
    username: str,
    password: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[bytes, SessionInfo]:
    login_host, _base = parse_host(host)
    client = KvmHttpClient(login_host, timeout=timeout)
    kvm_type, str_url = detect_kvm_type(client)

    if kvm_type == "old":
        session_id = _login_old(client, username, password)
        body, _ = _request(client, f"/JavaClient.jnlp?pid={session_id}")
        info = SessionInfo(
            kvm_type=kvm_type,
            jnlp_url=f"https://{login_host}/JavaClient.jnlp?pid={session_id}",
            session_id=session_id,
        )
        return body, info

    assert str_url is not None
    session_id = _login_new(client, str_url, username, password, login_host)
    body, _ = _request(client, "/Inquery.jnlp", cookie=f"sid={session_id}")
    info = SessionInfo(
        kvm_type=kvm_type,
        jnlp_url=f"https://{login_host}/Inquery.jnlp",
        session_id=session_id,
        str_url=str_url,
    )
    return body, info


def validate_jnlp(content: bytes) -> None:
    text = content.decode("utf-8", errors="replace")
    if "<jnlp" not in text.lower():
        raise JnlpError("error.jnlp.invalid")
