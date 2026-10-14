"""Typed contracts for importing a roster from CSV (S3-11)."""

from pydantic import BaseModel, Field


class RosterImportRequest(BaseModel):
    """The spreadsheet saved as CSV, sent as text (no file upload needed)."""

    csv: str = Field(min_length=1, max_length=2_000_000)


class ImportProblem(BaseModel):
    """A problem on one spreadsheet row (row 1 is the header)."""

    row: int
    message: str


class RosterImportSummary(BaseModel):
    """What an import would do (preview) or did (import)."""

    rows: int
    children_to_add: int
    children_skipped: int
    guardians_new: int
    guardians_existing: int
    assigned_to_routes: int
    problems: list[ImportProblem]
    imported: bool
