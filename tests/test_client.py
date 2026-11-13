import base64
import hashlib
import hmac
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from src.onshape_client import OnshapeClient, OnshapeHTTPError


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response


class OnshapeClientTests(unittest.TestCase):
    def test_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Fresh Onshape credentials"):
                OnshapeClient()

    def test_https_origin_required(self):
        with self.assertRaisesRegex(ValueError, "HTTPS origin"):
            OnshapeClient(base_url="http://example.org", access_key="abc", secret_key="xyz")

    def test_get_signs_path_and_query_on_separate_lines(self):
        fixed_time = datetime(2021, 1, 1, tzinfo=timezone.utc)
        session = FakeSession(FakeResponse(payload={"ok": True}))
        client = OnshapeClient(
            access_key="access",
            secret_key="secret",
            session=session,
            nonce_factory=lambda: "0123456789abcdef",
            now_factory=lambda: fixed_time,
        )

        result = client.get("/api/v13/example", [("b", "two words"), ("a", 1)])

        self.assertEqual({"ok": True}, result)
        method, url, kwargs = session.calls[0]
        self.assertEqual("GET", method)
        self.assertEqual("https://cad.onshape.com/api/v13/example?b=two+words&a=1", url)
        canonical = (
            "get\n0123456789abcdef\nfri, 01 jan 2021 00:00:00 gmt\n"
            "application/json\n/api/v13/example\nb=two+words&a=1\n"
        )
        expected = base64.b64encode(
            hmac.new(b"secret", canonical.encode(), hashlib.sha256).digest()
        ).decode()
        self.assertEqual(
            f"On access:HmacSHA256:{expected}", kwargs["headers"]["Authorization"]
        )
        self.assertEqual(30.0, kwargs["timeout"])

    def test_rejects_query_embedded_in_path(self):
        client = OnshapeClient(access_key="access", secret_key="secret")
        with self.assertRaisesRegex(ValueError, "pass query values"):
            client.get("/api/v13/example?a=1")

    def test_http_error_does_not_include_response_body(self):
        secret_body = "proprietary payload"
        session = FakeSession(FakeResponse(status_code=403, payload={"message": secret_body}))
        client = OnshapeClient(access_key="access", secret_key="secret", session=session)
        with self.assertRaises(OnshapeHTTPError) as raised:
            client.get("/api/v13/example")
        self.assertIn("HTTP 403", str(raised.exception))
        self.assertNotIn(secret_body, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
