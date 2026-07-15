"""HTTP/1.0-транспорт для ATEN CN8000 — прошивка рвёт HTTP/1.1 POST."""

from __future__ import annotations

import concurrent.futures
import gzip
import http.client
import re
import socket
import ssl
from urllib.parse import urlparse

DEFAULT_TIMEOUT = 15.0
DNS_TIMEOUT = 10.0


class KvmHttpError(Exception):
    """Ошибка транспорта с машинным кодом для i18n."""

    def __init__(self, code: str, **params: str) -> None:
        self.code = code
        self.params = params
        super().__init__(code)


def _legacy_ssl_context() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
    except ssl.SSLError:
        pass
    if hasattr(ssl, "TLSVersion"):
        ctx.minimum_version = ssl.TLSVersion.TLSv1
    return ctx


def parse_host(host: str) -> tuple[str, str]:
    """Вернуть (имя_хоста, базовый_URL)."""
    host = host.strip().rstrip("/")
    if host.startswith("http://") or host.startswith("https://"):
        parsed = urlparse(host)
        hostname = parsed.hostname or host
        scheme = parsed.scheme or "https"
        if parsed.port and parsed.port not in (80, 443):
            base = f"{scheme}://{hostname}:{parsed.port}"
        else:
            base = f"{scheme}://{hostname}"
        return hostname, base
    return host, f"https://{host}"


def _resolve_ipv4(hostname: str, *, timeout: float = DNS_TIMEOUT) -> str:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(socket.gethostbyname, hostname)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            raise KvmHttpError("dns_timeout", host=hostname) from exc
        except socket.gaierror as exc:
            raise KvmHttpError("dns_failed", host=hostname, detail=str(exc)) from exc


class KvmHttpClient:
    """Минимальный клиент: TLS 1.0 + HTTP/1.0 + IPv4 + gzip."""

    def __init__(self, hostname: str, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.hostname = hostname
        self.timeout = timeout
        self._ip = _resolve_ipv4(hostname, timeout=min(timeout, DNS_TIMEOUT))
        self._ssl = _legacy_ssl_context()

    def request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        cookie: str | None = None,
        content_type: str | None = None,
    ) -> tuple[bytes, dict[str, str]]:
        if not path.startswith("/"):
            path = f"/{path}"

        conn = http.client.HTTPSConnection(self._ip, 443, context=self._ssl, timeout=self.timeout)
        conn._http_vsn = 10
        conn._http_vsn_str = "HTTP/1.0"

        headers = {
            "Host": self.hostname,
            "User-Agent": "CN8000A-Portable-Launcher/0.2",
            "Connection": "close",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        if body is not None:
            headers["Content-Type"] = content_type or "application/x-www-form-urlencoded"
            headers["Content-Length"] = str(len(body))
        if cookie:
            headers["Cookie"] = cookie

        try:
            conn.request(method, path, body=body, headers=headers)
            resp = conn.getresponse()
            data = resp.read()
            hdrs = {k.lower(): v for k, v in resp.getheaders()}
            if resp.status >= 400:
                raise KvmHttpError("http_status", status=str(resp.status), path=path)
        except TimeoutError as exc:
            raise KvmHttpError("timeout", seconds=str(int(self.timeout))) from exc
        except OSError as exc:
            if "timed out" in str(exc).lower():
                raise KvmHttpError("timeout", seconds=str(int(self.timeout))) from exc
            raise KvmHttpError("connection_failed", path=path, detail=str(exc)) from exc
        except http.client.HTTPException as exc:
            raise KvmHttpError("connection_failed", path=path, detail=str(exc)) from exc
        finally:
            conn.close()

        if hdrs.get("content-encoding") == "gzip":
            try:
                data = gzip.decompress(data)
            except OSError:
                pass

        return data, hdrs

    @staticmethod
    def extract_sid(headers: dict[str, str]) -> str | None:
        cookie = headers.get("set-cookie", "")
        match = re.search(r"sid=(\w+)", cookie, flags=re.IGNORECASE)
        return match.group(1) if match else None
