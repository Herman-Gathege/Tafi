"""Shared field types."""

import re
from typing import Annotated

from pydantic import AfterValidator

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_SEPARATORS = re.compile(r"[\s\-().]")
_PHONE_HINT = "Enter a phone number like 0712 345 678 or +254 712 345 678"
_MOBILE_HINT = "Enter a mobile number like 0712 345 678 or +254 712 345 678"


def normalise_email(value: str) -> str:
    """Lower-case and trim an address, rejecting obvious nonsense."""
    email = value.strip().lower()
    if not _EMAIL.match(email):
        raise ValueError("Enter a valid email address")
    return email


def normalise_phone(value: str, *, mobile_only: bool = False) -> str:
    """Return a phone number in E.164 (+254712345678).

    Accepts the ways Kenyans write numbers: 0712 345 678, 712345678, 254712345678,
    +254 712 345 678, 00254… Numbers from other countries must start with + or 00.
    With `mobile_only`, a Kenyan number must be a mobile (07… or 01…), as WhatsApp needs.
    """
    raw = _PHONE_SEPARATORS.sub("", value.strip())
    hint = _MOBILE_HINT if mobile_only else _PHONE_HINT
    if raw.startswith("00"):
        raw = "+" + raw[2:]

    if raw.startswith("+"):
        digits = raw[1:]
    elif raw.startswith("254") and len(raw) == 12:
        digits = raw
    elif raw.startswith("0") and len(raw) == 10:
        digits = "254" + raw[1:]
    elif len(raw) == 9 and raw[0] in "17":
        digits = "254" + raw
    else:
        raise ValueError(hint)

    if not digits.isdigit() or not 8 <= len(digits) <= 15 or digits.startswith("0"):
        raise ValueError(hint)
    if digits.startswith("254"):
        if len(digits) != 12:
            raise ValueError(hint)
        if mobile_only and digits[3] not in "17":
            raise ValueError(hint)
    return "+" + digits


def normalise_mobile(value: str) -> str:
    """A WhatsApp-capable number in E.164."""
    return normalise_phone(value, mobile_only=True)


Email = Annotated[str, AfterValidator(normalise_email)]
Phone = Annotated[str, AfterValidator(normalise_phone)]
WhatsAppNumber = Annotated[str, AfterValidator(normalise_mobile)]
