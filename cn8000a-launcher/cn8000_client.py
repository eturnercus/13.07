"""ATEN CN8000 / CN8000A KVM login and JNLP download.

Adapted from https://github.com/sagb/cn8000-cli (MIT-style community script).
Supports legacy CN8000 web interfaces that require TLS 1.0 and weak ciphers.
"""

from __future__ import annotations

import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Literal


KvmType = Literal["old", "new"]


@dataclass
class SessionInfo:
    kvm_type: KvmType
    jnlp_url: str
    session_id: str | None = None
    str_url: str | None = None


class Cn8000Error(Exception):
    """Base error for CN8000 client operations."""


class LoginError(Cn8000Error):
    """Authentication or session creation failed."""


class JnlpError(Cn8000Error):
    """JNLP file could not be retrieved."""


def _legacy_ssl_context() -> ssl.SSLContext:
    """Build an SSL context that can talk to old ATEN firmware."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    # OpenSSL 3+ may need explicit legacy re-enablement; ignore if unsupported.
    try:
        ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
    except ssl.SSLError:
        pass
    if hasattr(ssl, "TLSVersion"):
        ctx.minimum_version = ssl.TLSVersion.TLSv1
    return ctx


def _request(
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    cookie: str | None = None,
    method: str | None = None,
    timeout: float = 30.0,
) -> tuple[bytes, dict[str, str]]:
    hdrs = {
        "User-Agent": "CN8000A-Portable-Launcher/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if headers:
        hdrs.update(headers)
    if cookie:
        hdrs["Cookie"] = cookie

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, context=_legacy_ssl_context(), timeout=timeout) as resp:
            body = resp.read()
            response_headers = {k.lower(): v for k, v in resp.headers.items()}
            return body, response_headers
    except urllib.error.HTTPError as exc:
        body = exc.read()
        response_headers = {k.lower(): v for k, v in exc.headers.items()}
        return body, response_headers
    except urllib.error.URLError as exc:
        raise Cn8000Error(f"Network error while contacting {url}: {exc}") from exc


def _site(host: str, *, https: bool = True) -> str:
    host = host.strip()
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    scheme = "https" if https else "http"
    return f"{scheme}://{host}"


def detect_kvm_type(site: str) -> tuple[KvmType, str | None]:
    body, _ = _request(f"{site}/")
    text = body.decode("utf-8", errors="replace")
    match = re.search(r'strURL.*\+\s*"/(\w+?)"', text)
    if match:
        return "new", match.group(1)
    return "old", None


def _login_old(site: str, username: str, password: str) -> str:
    ts = time.strftime("%Y.%m.%d.%H.%M.%S.") + f"{int(time.time() * 1000)}000.-180"
    form = urllib.parse.urlencode(
        {
            "username": username,
            "password": password,
            "login": "Login",
            "curtime": ts,
        }
    ).encode("ascii")
    body, _ = _request(
        f"{site}/view.htm",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    text = body.decode("utf-8", errors="replace")
    match = re.search(r"global_sessionpid='(\w+?)'", text)
    if not match:
        raise LoginError("Login failed: session id not returned by CN8000 (check host/credentials).")
    return match.group(1)


def _login_new(site: str, str_url: str, username: str, password: str, host: str) -> tuple[str, str]:
    page_body, _ = _request(f"{site}/{str_url}")
    page = page_body.decode("utf-8", errors="replace")
    tid_match = re.search(r'name="KVMIP_TARGETID" value="(\w+?)"', page)
    if not tid_match:
        raise LoginError("Login failed: KVM target id not found on device page.")
    target_id = tid_match.group(1)

    login_value = f"{username}+{password}+{host}+{target_id}"
    form = urllib.parse.urlencode(
        {
            "KVMIP_GMTIME": str(int(time.time())),
            "KVMIP_DIFFTIME": "420",
            "KVMIP_LOGIN": login_value,
            "KVMIP_TARGETID": target_id,
        }
    ).encode("ascii")

    _, headers = _request(
        f"{site}/{str_url}",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    set_cookie = headers.get("set-cookie", "")
    sid_match = re.search(r"sid=(\S+)", set_cookie)
    if not sid_match:
        raise LoginError("Login failed: session cookie not returned by CN8000.")
    sid = sid_match.group(1).rstrip(";")

    xid = f"0.{int(time.time() * 1_000_000) % 10**17:017d}"
    inquery_form = urllib.parse.urlencode(
        {
            "/Inquery?update": "31",
            "com_common": "01",
            "xid": xid,
            "SID": sid,
        }
    ).encode("ascii")
    inquery_body, _ = _request(
        f"{site}/Inquery",
        data=inquery_form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        cookie=f"sid={sid}",
        method="POST",
    )
    if inquery_body.decode("utf-8", errors="replace").strip() != "u":
        # Device sometimes still works; keep going like the reference script.
        pass

    return sid, f"{site}/Inquery.jnlp"


def fetch_jnlp(host: str, username: str, password: str) -> tuple[bytes, SessionInfo]:
    """Authenticate against CN8000(A) and download the Java viewer JNLP."""
    site = _site(host)
    kvm_type, str_url = detect_kvm_type(site)

    if kvm_type == "old":
        session_id = _login_old(site, username, password)
        jnlp_url = f"{site}/JavaClient.jnlp?pid={session_id}"
        body, _ = _request(jnlp_url)
        info = SessionInfo(kvm_type=kvm_type, jnlp_url=jnlp_url, session_id=session_id)
        return body, info

    assert str_url is not None
    session_id, jnlp_url = _login_new(site, str_url, username, password, host)
    body, _ = _request(jnlp_url, cookie=f"sid={session_id}")
    info = SessionInfo(
        kvm_type=kvm_type,
        jnlp_url=jnlp_url,
        session_id=session_id,
        str_url=str_url,
    )
    return body, info


def validate_jnlp(content: bytes) -> None:
    text = content.decode("utf-8", errors="replace")
    if "<jnlp" not in text.lower():
        raise JnlpError("Downloaded file does not look like a JNLP document.")
