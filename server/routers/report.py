from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models.user import User
from db.session import get_db
from dependencies import get_optional_user
from schemas.report import GenerateReportRequest, ReportData
from services.question_pipeline import run_report_pipeline
from services.quiz_sync_service import sync_quiz_result

router = APIRouter(prefix="/api/v1/report", tags=["report"])


@router.post("/generate", response_model=ReportData, response_model_by_alias=True)
async def generate_report(
    request: GenerateReportRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> ReportData:
    report = await run_report_pipeline(request)

    if current_user is None:
        return report

    try:
        exp_gain, stats = sync_quiz_result(db, current_user, request, report)
        report.exp_gain = exp_gain
        report.stats = stats
        db.commit()
    except Exception:
        db.rollback()
        report.sync_failed = True

    return report
