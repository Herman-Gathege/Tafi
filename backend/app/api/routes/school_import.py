"""Import children and guardians from a spreadsheet (Sprint 3: S3-11).

Preview first, then import. The import checks every row again and saves nothing if any row
has a problem.
"""

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession, SchoolAdmin
from app.api.routes.school_students import link_guardian, today
from app.models.student import Student
from app.models.transport import StudentRouteAssignment
from app.schemas.roster_import import ImportProblem, RosterImportRequest, RosterImportSummary
from app.schemas.students import GuardianInput
from app.services.roster_import import ImportPlan, plan_import

router = APIRouter(prefix="/api/v1/school/students/import", tags=["school"])

UNPROCESSABLE = 422


def summary(plan: ImportPlan, *, imported: bool) -> RosterImportSummary:
    return RosterImportSummary(
        rows=plan.rows,
        children_to_add=len(plan.to_add),
        children_skipped=plan.skipped,
        guardians_new=plan.guardians_new,
        guardians_existing=plan.guardians_existing,
        assigned_to_routes=plan.assigned_to_routes,
        problems=[ImportProblem(row=row, message=message) for row, message in plan.problems],
        imported=imported,
    )


@router.post("/preview", response_model=RosterImportSummary)
def preview_import(
    payload: RosterImportRequest, admin: SchoolAdmin, db: DbSession
) -> RosterImportSummary:
    """Check every row and say what an import would do. Saves nothing."""
    return summary(plan_import(db, admin.organization_id, payload.csv), imported=False)


@router.post("", response_model=RosterImportSummary)
def run_import(
    payload: RosterImportRequest, admin: SchoolAdmin, db: DbSession
) -> RosterImportSummary:
    """Import every row, or none: any problem stops the whole import."""
    plan = plan_import(db, admin.organization_id, payload.csv)
    if plan.problems:
        count = len(plan.problems)
        raise HTTPException(
            UNPROCESSABLE,
            f"Nothing was imported: {count} row{'s' if count > 1 else ''} need fixing. "
            "Preview the file to see them.",
        )
    for child in plan.to_add:
        student = Student(
            organization_id=admin.organization_id,
            first_name=child.first_name,
            last_name=child.last_name,
            grade=child.grade,
        )
        db.add(student)
        db.flush()
        for position, guardian in enumerate(child.guardians):
            link_guardian(
                db,
                admin,
                student,
                GuardianInput(
                    full_name=guardian.full_name,
                    whatsapp_number=guardian.whatsapp_number,
                    relationship=guardian.relationship,
                    is_primary=position == 0,
                ),
            )
        if child.route is not None:
            db.add(
                StudentRouteAssignment(
                    organization_id=admin.organization_id,
                    student_id=student.id,
                    route_id=child.route.id,
                    pickup_stop_id=child.pickup.id if child.pickup else None,
                    dropoff_stop_id=child.dropoff.id if child.dropoff else None,
                    active_from=today(),
                )
            )
    db.commit()
    return summary(plan, imported=True)
