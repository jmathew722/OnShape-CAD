"""Small, read-only Onshape REST client using API-key HMAC authentication."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone
from email.utils import format_datetime
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlencode, urlsplit

import requests


class OnshapeError(RuntimeError):
    """Base error for safe, user-facing Onshape failures."""


class OnshapeHTTPError(OnshapeError):
    """HTTP failure that deliberately excludes response bodies and credentials."""


Params = Mapping[str, Any] | Sequence[tuple[str, Any]] | None


class OnshapeClient:
    """Authenticated GET-only client.

    The class intentionally exposes no POST, PUT, PATCH, or DELETE operation. Write
    support belongs in a separate, approval-gated implementation after a dry run.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        timeout: float = 30.0,
        session: requests.Session | None = None,
        nonce_factory: Callable[[], str] | None = None,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com")).rstrip("/")
        self.access_key = access_key or os.environ.get("ONSHAPE_ACCESS_KEY", "")
        self._secret_key = secret_key or os.environ.get("ONSHAPE_SECRET_KEY", "")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._nonce_factory = nonce_factory or (lambda: secrets.token_hex(16))
        self._now_factory = now_factory or (lambda: datetime.now(timezone.utc))

        if not self.access_key or not self._secret_key:
            raise RuntimeError(
                "Fresh Onshape credentials are required in ONSHAPE_ACCESS_KEY and "
                "ONSHAPE_SECRET_KEY"
            )
        parsed = urlsplit(self.base_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("ONSHAPE_BASE_URL must be an HTTPS origin without a path, query, or fragment")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

    @staticmethod
    def _encode_query(params: Params) -> str:
        return urlencode(params or {}, doseq=True)

    def _auth_headers(self, method: str, path: str, query: str = "") -> dict[str, str]:
        nonce = self._nonce_factory()
        if len(nonce) < 16 or not nonce.isalnum():
            raise ValueError("Onshape nonce must be unique, alphanumeric, and at least 16 characters")

        now = self._now_factory()
        if now.tzinfo is None:
            raise ValueError("now_factory must return a timezone-aware datetime")
        date = format_datetime(now.astimezone(timezone.utc), usegmt=True)
        content_type = "application/json"
        canonical = "\n".join((method.upper(), nonce, date, content_type, path, query, "")).lower()
        digest = hmac.new(
            self._secret_key.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256
        ).digest()
        signature = base64.b64encode(digest).decode("ascii")
        return {
            "Authorization": f"On {self.access_key}:HmacSHA256:{signature}",
            "On-Nonce": nonce,
            "Date": date,
            "Content-Type": content_type,
            "Accept": "application/json",
        }

    def get(self, path: str, params: Params = None) -> Any:
        """Perform an authenticated GET and decode its JSON response."""
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("path must be an absolute API path; pass query values through params")
        if not parsed.path.startswith("/api/"):
            raise ValueError("Expected an Onshape API path beginning /api/")

        query = self._encode_query(params)
        headers = self._auth_headers("GET", parsed.path, query)
        url = f"{self.base_url}{parsed.path}"
        if query:
            url = f"{url}?{query}"
        try:
            response = self._session.request("GET", url, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise OnshapeHTTPError(f"Onshape request failed before a response: {type(exc).__name__}") from exc

        if not 200 <= response.status_code < 300:
            request_id = response.headers.get("On-Request-Id") or response.headers.get("X-Request-Id")
            suffix = f" (request id: {request_id})" if request_id else ""
            raise OnshapeHTTPError(f"Onshape returned HTTP {response.status_code}{suffix}")
        try:
            return response.json()
        except ValueError as exc:
            raise OnshapeHTTPError("Onshape returned a successful response that was not valid JSON") from exc
