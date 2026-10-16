"""Phone numbers arrive the way people write them and are stored in E.164."""

import pytest

from app.schemas.common import normalise_mobile, normalise_phone


@pytest.mark.parametrize(
    "written",
    [
        "0712345678",
        "0712 345 678",
        "0712-345-678",
        "712345678",
        "254712345678",
        "+254712345678",
        "+254 712 345 678",
        "(+254) 712 345678",
        "00254712345678",
    ],
)
def test_kenyan_mobile_numbers_in_every_usual_form(written: str) -> None:
    assert normalise_mobile(written) == "+254712345678"


def test_newer_01_prefixes_are_mobiles_too() -> None:
    assert normalise_mobile("0110 123 456") == "+254110123456"


def test_a_landline_is_a_phone_but_not_a_whatsapp_number() -> None:
    assert normalise_phone("020 123 4567") == "+254201234567"
    with pytest.raises(ValueError):
        normalise_mobile("020 123 4567")


def test_numbers_from_other_countries_need_a_plus() -> None:
    assert normalise_mobile("+255 754 123 456") == "+255754123456"
    assert normalise_mobile("0044 7700 900123") == "+447700900123"


@pytest.mark.parametrize(
    "written",
    ["", "hello", "07123", "07123456789", "+2547123456", "+254 712 345 678 9", "+0712345678"],
)
def test_nonsense_is_refused(written: str) -> None:
    with pytest.raises(ValueError):
        normalise_mobile(written)
