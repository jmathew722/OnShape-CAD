"""Minimal Onshape HMAC-authenticated REST client; GET-only by design."""
import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests


class OnshapeClient:
    def __init__(self):
        self.base_url = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com").rstrip("/")
        self.access_key = os.environ.get("ONSHAPE_ACCESS_KEY", "")
        self.secret_key = os.environ.get("ONSHAPE_SECRET_KEY", "")
        if not self.access_key or not self.secret_key:
            raise RuntimeError("Set ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY in your environment")
        if not self.base_url.startswith("https://"):
            raise ValueError("ONSHAPE_BASE_URL must use https")

    def get(self, path, params=None):
        """Perform a read-only API request. Mutating methods are intentionally absent."""
        if not path.startswith("/api/"):
            raise ValueError("Expected an Onshape API path beginning /api/")
        params = params or {}
        query = urlencode(params, doseq=True)
        uri = f"{path}?{query}" if query else path
        nonce = secrets.token_hex(16)
        date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        content_type = "application/json"
        canonical = f"GET\n{nonce}\n{date}\n{content_type}\n{uri}\n".lower()
        signature = base64.b64encode(hmac.new(self.secret_key.encode(), canonical.encode(), hashlib.sha256).digest()).decode()
        headers = {
            "Authorization": f"On {self.access_key}:HmacSHA256:{signature}",
            "On-Nonce": nonce,
            "Date": date,
            "Content-Type": content_type,
            "Accept": "application/json",
        }
        response = requests.get(f"{self.base_url}{uri}", headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
