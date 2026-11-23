"""Payment requests. Sensitive code: see services/payments/AGENTS.md."""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

log = logging.getLogger(__name__)

DEFAULT_PAYMENTS_URL = "https://payments.example.com/v1/charges"

Post = Callable[[str, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class Charge:
    payment_id: str
    order_id: str
    amount_cents: int


class ConfigError(RuntimeError):
    """Missing or unsafe configuration."""


def validate_amount_cents(amount_cents: object) -> int:
    """Return the amount if it is a positive int of cents; raise ValueError otherwise."""
    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents <= 0:
        raise ValueError("amount_cents must be a positive integer")
    return amount_cents


def payments_url() -> str:
    """The payments endpoint. Must be HTTPS, so the bearer token is never sent in clear text."""
    url = os.environ.get("PAYMENTS_URL", DEFAULT_PAYMENTS_URL)
    if urlsplit(url).scheme != "https":
        raise ConfigError("PAYMENTS_URL must use https")
    return url


def payments_token() -> str:
    token = os.environ.get("PAYMENTS_TOKEN", "")
    if not token:
        raise ConfigError("PAYMENTS_TOKEN is not set")
    return token


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """urllib would copy the Authorization header to a redirect target on another host. Refuse instead."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise urllib.error.HTTPError(req.full_url, code, "redirects are not followed for payments", headers, fp)


_opener = urllib.request.build_opener(_NoRedirect)


def http_post(url: str, body: dict[str, Any]) -> dict[str, Any]:
    """Default transport. The API token comes from the environment, never from code."""
    if urlsplit(url).scheme != "https":
        raise ConfigError("payments requests must use https")
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {payments_token()}"},
        method="POST",
    )
    with _opener.open(request, timeout=5) as response:
        return json.load(response)


def create_charge(order_id: str, amount_cents: int, post: Post = http_post) -> Charge:
    if not isinstance(order_id, str) or not order_id:
        raise ValueError("order_id must be a non-empty string")
    validate_amount_cents(amount_cents)
    result = post(payments_url(), {"order_id": order_id, "amount_cents": amount_cents})
    payment_id = result.get("payment_id")
    if not isinstance(payment_id, str) or not payment_id:
        raise RuntimeError("payment service returned no payment_id")
    # Payment ID only, never card or customer details. %r stops a crafted ID from forging log lines.
    log.info("charge created: %r", payment_id)
    return Charge(payment_id=payment_id, order_id=order_id, amount_cents=amount_cents)
