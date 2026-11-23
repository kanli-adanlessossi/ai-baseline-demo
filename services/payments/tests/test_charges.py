import logging

import pytest

from payments.charges import Charge, create_charge, validate_amount_cents


def fake_post(response):
    calls = []

    def post(url, body):
        calls.append((url, body))
        return response

    post.calls = calls
    return post


def test_create_charge_returns_charge():
    post = fake_post({"payment_id": "pay_123"})
    assert create_charge("A1", 2599, post=post) == Charge("pay_123", "A1", 2599)
    assert post.calls[0][1] == {"order_id": "A1", "amount_cents": 2599}


@pytest.mark.parametrize("bad", [0, -5, 25.99, True, "2599", None])
def test_rejects_invalid_amounts(bad):
    with pytest.raises(ValueError):
        validate_amount_cents(bad)


def test_rejects_empty_order_id():
    with pytest.raises(ValueError):
        create_charge("", 100, post=fake_post({"payment_id": "pay_1"}))


def test_missing_payment_id_is_an_error():
    with pytest.raises(RuntimeError):
        create_charge("A1", 100, post=fake_post({}))


def test_logs_payment_id_only(caplog):
    with caplog.at_level(logging.INFO):
        create_charge("A1", 100, post=fake_post({"payment_id": "pay_9", "card_last4": "4242"}))
    assert "pay_9" in caplog.text
    assert "4242" not in caplog.text


# --- security: where the token can go ---

import urllib.error
import urllib.request

from payments.charges import ConfigError, _NoRedirect, http_post, payments_token, payments_url


def test_payments_url_must_be_https(monkeypatch):
    monkeypatch.setenv("PAYMENTS_URL", "http://payments.example.com/v1/charges")
    with pytest.raises(ConfigError):
        payments_url()
    with pytest.raises(ConfigError):
        create_charge("A1", 100, post=fake_post({"payment_id": "pay_1"}))


def test_http_post_refuses_plain_http(monkeypatch):
    monkeypatch.setenv("PAYMENTS_TOKEN", "test-token-not-real")
    with pytest.raises(ConfigError):
        http_post("http://payments.example.com/v1/charges", {})


def test_missing_token_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("PAYMENTS_TOKEN", raising=False)
    with pytest.raises(ConfigError, match="PAYMENTS_TOKEN"):
        payments_token()


def test_redirects_are_refused_so_the_token_is_not_forwarded():
    request = urllib.request.Request("https://payments.example.com/v1/charges", method="POST",
                                     headers={"Authorization": "Bearer x"})
    with pytest.raises(urllib.error.HTTPError):
        _NoRedirect().redirect_request(request, None, 302, "Found", {}, "https://elsewhere.example/steal")


def test_log_line_cannot_be_forged(caplog):
    with caplog.at_level(logging.INFO):
        create_charge("A1", 100, post=fake_post({"payment_id": "pay_1\nadmin login ok"}))
    assert "\nadmin login ok" not in caplog.text
