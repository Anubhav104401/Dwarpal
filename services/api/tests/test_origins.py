"""Origins, written one way (decision D29): what a project may allow, and how a return address's origin is read."""

from __future__ import annotations

import pytest

from dwarpal_api.domain.origins import MAX_ORIGINS, InvalidOriginError, allowed_origin, allowed_origins, origin_of


@pytest.mark.parametrize(
    ("text", "origin"),
    [
        ("https://shop.example", "https://shop.example"),
        ("HTTPS://Shop.Example/", "https://shop.example"),
        ("https://shop.example:443", "https://shop.example"),
        ("https://shop.example:8443", "https://shop.example:8443"),
        ("https://xn--bcher-kva.example", "https://xn--bcher-kva.example"),
        ("https://192.0.2.7", "https://192.0.2.7"),
        ("https://[2001:DB8::1]:8443", "https://[2001:db8::1]:8443"),
        ("  https://shop.example  ", "https://shop.example"),
    ],
)
def test_an_origin_is_written_the_way_browsers_write_it(text: str, origin: str) -> None:
    assert allowed_origin(text, production=True) == origin


@pytest.mark.parametrize(
    "text",
    [
        "https://shop.example/cellar",
        "https://shop.example?x=1",
        "https://shop.example#top",
        "https://ana:secret@shop.example",
        "https://*.shop.example",
        "https://shop_example.example",
        "https://shop.example:0",
        "https://shop.example:99999",
        "ftp://shop.example",
        "shop.example",
        "http://shop.example",
        "",
    ],
)
def test_anything_but_an_origin_is_refused(text: str) -> None:
    with pytest.raises(InvalidOriginError):
        allowed_origin(text, production=False)


def test_http_is_allowed_only_for_this_computer_and_never_in_production() -> None:
    assert allowed_origin("http://localhost:3100", production=False) == "http://localhost:3100"
    assert allowed_origin("http://127.0.0.1", production=False) == "http://127.0.0.1"
    with pytest.raises(InvalidOriginError, match="https"):
        allowed_origin("http://localhost:3100", production=True)


def test_a_list_keeps_its_order_drops_duplicates_and_has_a_limit() -> None:
    assert allowed_origins(["https://b.example", "https://a.example", "HTTPS://b.example/"], production=True) == [
        "https://b.example",
        "https://a.example",
    ]
    too_many = [f"https://s{i}.example" for i in range(MAX_ORIGINS + 1)]
    with pytest.raises(InvalidOriginError, match="at most"):
        allowed_origins(too_many, production=True)


def test_a_return_address_is_reduced_to_its_origin() -> None:
    assert origin_of("https://SHOP.example:443/age-check/done?x=1#y") == "https://shop.example"
    assert origin_of("http://localhost:3100/age-check/complete") == "http://localhost:3100"
    with pytest.raises(InvalidOriginError):
        origin_of("javascript:alert(1)")
