"""Guardian consent to WhatsApp messages (S3-06, D-22).

No message goes to a guardian without a current consent. Sprint 5 calls `can_message` before
sending anything. Consent rows are append-only: withdrawing stamps `withdrawn_at`; consenting
again adds a new row, so the history shows who agreed to which wording, how and when.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.models.guardian import ConsentMethod, Guardian, GuardianConsent

# The wording a guardian agrees to. Change the version whenever the text changes, so every
# consent record shows exactly what was agreed. DRAFT: the client (and their lawyer) must
# approve it before the pilot (MVP-22, Kenya Data Protection Act 2019).
CONSENT_VERSION = "2026-10-draft"
CONSENT_TEXT = (
    "{school_name} uses Tafi to keep you informed about your child's school transport.\n\n"
    "If you agree:\n"
    "• You will get WhatsApp messages when your child gets on and off the school vehicle, "
    "when the vehicle is near your stop, and when it is running late.\n"
    "• The school and Tafi keep your name, phone number and your child's trip records while "
    "your child uses school transport, and for up to 12 months after.\n"
    "• These details are shared only with the school and the Tafi team who run the service. "
    "They are never sold or used for advertising.\n\n"
    "You can stop the messages at any time by telling the school. Questions about your data: "
    "[privacy contact to be confirmed]."
)


def consent_text(school_name: str) -> str:
    return CONSENT_TEXT.format(school_name=school_name)


def current_consent(db: Session, guardian_id: uuid.UUID) -> GuardianConsent | None:
    """The latest consent that has not been withdrawn."""
    return db.scalar(
        select(GuardianConsent)
        .where(GuardianConsent.guardian_id == guardian_id, GuardianConsent.withdrawn_at.is_(None))
        .order_by(GuardianConsent.given_at.desc())
        .limit(1)
    )


def can_message(db: Session, guardian: Guardian) -> bool:
    """True only when the guardian has a current consent. Check before every message."""
    return current_consent(db, guardian.id) is not None


def consented_guardian_ids(db: Session, guardian_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    """Which of these guardians may be messaged, in one query."""
    if not guardian_ids:
        return set()
    return set(
        db.scalars(
            select(GuardianConsent.guardian_id).where(
                GuardianConsent.guardian_id.in_(guardian_ids),
                GuardianConsent.withdrawn_at.is_(None),
            )
        )
    )


def record_consent(
    db: Session,
    guardian: Guardian,
    *,
    method: ConsentMethod,
    version: str = CONSENT_VERSION,
    recorded_by_user_id: uuid.UUID | None = None,
) -> GuardianConsent:
    """Add a consent. An existing current consent is left as it is (no duplicate)."""
    existing = current_consent(db, guardian.id)
    if existing is not None and existing.consent_version == version:
        return existing
    if existing is not None:
        existing.withdrawn_at = utcnow()  # superseded by consent to newer wording
    consent = GuardianConsent(
        organization_id=guardian.organization_id,
        guardian_id=guardian.id,
        consent_version=version,
        method=method,
        given_at=utcnow(),
        recorded_by_user_id=recorded_by_user_id,
    )
    db.add(consent)
    db.flush()
    return consent


def withdraw_consent(db: Session, guardian: Guardian) -> bool:
    """Stop all messages to a guardian. Returns False when there was nothing to withdraw."""
    consent = current_consent(db, guardian.id)
    if consent is None:
        return False
    consent.withdrawn_at = utcnow()
    db.flush()
    return True
