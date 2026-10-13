"""Operational commands. Run with `python -m app.cli --help`."""

import argparse
from collections.abc import Sequence

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.common import normalise_email


def create_platform_admin(email: str, password: str, name: str | None = None) -> str:
    """Create the first Tafi account, or promote an existing one.

    There is no self-signup: someone has to be able to make the first account.
    """
    address = normalise_email(email)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == address))
        if user is None:
            user = User(
                email=address,
                name=name or address.split("@")[0],
                password_hash=hash_password(password),
                is_platform_admin=True,
            )
            db.add(user)
            action = "created"
        else:
            user.is_platform_admin = True
            user.is_active = True
            user.password_hash = hash_password(password)
            if name:
                user.name = name
            action = "promoted"
        db.commit()
        return f"Platform admin {action}: {address}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.cli", description="Tafi operations")
    subcommands = parser.add_subparsers(dest="command", required=True)

    admin = subcommands.add_parser(
        "create-platform-admin", help="create (or promote) a Tafi staff account"
    )
    admin.add_argument("--email", required=True)
    admin.add_argument("--password", required=True)
    admin.add_argument("--name", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "create-platform-admin":
        print(create_platform_admin(args.email, args.password, args.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
