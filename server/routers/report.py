from fastapi import APIRouter

from schemas.report import GenerateReportRequest, ReportData
from services.question_pipeline import compute_report_stats, run_report_pipeline

router = APIRouter(prefix="/api/v1/report", tags=["report"])


@router.post("/generate", response_model=ReportData, response_model_by_alias=True)
async def generate_report(request: GenerateReportRequest) -> ReportData:
    return await run_report_pipeline(request)
