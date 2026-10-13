"""Shared field types."""

import re
from typing import Annotated

from pydantic import AfterValidator

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalise_email(value: str) -> str:
    """Lower-case and trim an address, rejecting obvious nonsense."""
    email = value.strip().lower()
    if not _EMAIL.match(email):
        raise ValueError("Enter a valid email address")
    return email


Email = Annotated[str, AfterValidator(normalise_email)]
