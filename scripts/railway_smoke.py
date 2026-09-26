#!/usr/bin/env python3
"""Minimal post-deploy smoke check for Railway beta.

Usage:
  QLDA_URL=https://your-frontend.up.railway.app \
  QLDA_ADMIN_USERNAME=admin \
  QLDA_ADMIN_PASSWORD='...' \
  python scripts/railway_smoke.py
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("QLDA_URL", "").rstrip("/")
USERNAME = os.environ.get("QLDA_ADMIN_USERNAME", "admin")
PASSWORD = os.environ.get("QLDA_ADMIN_PASSWORD", "")


def request(path: str, *, method: str = "GET", data=None, token: str | None = None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as res:
        raw = res.read().decode("utf-8")
        return res.status, json.loads(raw) if raw else None


def main() -> int:
    if not BASE or not PASSWORD:
        print("Missing QLDA_URL or QLDA_ADMIN_PASSWORD", file=sys.stderr)
        return 2

    try:
        status, health = request("/health")
        assert status == 200 and health.get("status") == "ok"
        print(f"PASS frontend health: {health}")

        status, login = request(
            "/api/auth/login",
            method="POST",
            data={"username": USERNAME, "password": PASSWORD},
        )
        assert status == 200 and login.get("access_token")
        token = login["access_token"]
        print(f"PASS login: {login.get('user', {}).get('username')}")

        status, me = request("/api/auth/me", token=token)
        assert status == 200 and me.get("username") == USERNAME
        print(f"PASS authenticated API: role={me.get('role')}")

        status, modules = request("/api/modules", token=token)
        assert status == 200 and isinstance(modules, list) and len(modules) >= 12
        print(f"PASS module registry: {len(modules)} modules")

        print("Railway beta smoke check PASSED")
        return 0
    except (AssertionError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"Railway beta smoke check FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
