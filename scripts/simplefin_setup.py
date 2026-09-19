#!/usr/bin/env python3
"""Claim a SimpleFIN Setup Token and store its Access URL locally."""
from __future__ import annotations

import argparse
import base64
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen


def claim_access_url(setup_token: str) -> str:
    try:
        claim_url = base64.b64decode(setup_token, validate=True).decode("utf-8").strip()
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("the Setup Token is not valid base64 text") from exc
    if not claim_url.startswith("https://"):
        raise ValueError("the decoded SimpleFIN claim URL must use HTTPS")
    request = Request(claim_url, method="POST", data=b"", headers={"Content-Length": "0"})
    with urlopen(request, timeout=30) as response:
        access_url = response.read().decode("utf-8").strip()
    if not access_url.startswith("https://"):
        raise ValueError("SimpleFIN returned an invalid Access URL")
    return access_url


def store_access_url(path: Path, access_url: str) -> None:
    path = path.expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(access_url + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)
    path.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description="Store a SimpleFIN Access URL for finplan-tui")
    parser.add_argument(
        "--output", type=Path,
        default=Path.home() / ".config" / "finplan-tui" / "simplefin-access-url",
    )
    args = parser.parse_args()
    token = input("Paste the one-time SimpleFIN Setup Token (not stored): ").strip()
    try:
        access_url = claim_access_url(token)
        store_access_url(args.output, access_url)
    except Exception as exc:
        parser.error(str(exc))
    print(f"Saved the protected SimpleFIN Access URL to {args.output.expanduser()}")
    print("Run: python3 app.py --simplefin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
