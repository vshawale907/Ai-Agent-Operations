"""
Reports API routes for executive report generation and file exports.

Supports live generation and direct binary/text streaming for CSV, PDF, and JSON.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.user import User
from app.schemas.agent_schemas import ExecutiveReport
from app.services.auth_service import get_current_user
from app.services.report_service import report_service

router = APIRouter()


class GenerateReportRequest(BaseModel):
    period: str = "Trailing 12 Months"


@router.post("/generate", response_model=ExecutiveReport)
async def generate_report(
    payload: GenerateReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a comprehensive executive business operations & analytics report."""
    return await report_service.generate_executive_report(db, payload.period)


@router.get("/export/csv")
async def export_report_csv(
    period: str = Query("Trailing 12 Months"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download executive report formatted as CSV."""
    report = await report_service.generate_executive_report(db, period)
    csv_content = report_service.export_report_csv(report)

    filename = f"executive_report_{period.lower().replace(' ', '_')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/pdf")
async def export_report_pdf(
    period: str = Query("Trailing 12 Months"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download executive report formatted as PDF document."""
    report = await report_service.generate_executive_report(db, period)
    pdf_bytes = report_service.export_report_pdf_bytes(report)

    filename = f"executive_report_{period.lower().replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/json")
async def export_report_json(
    period: str = Query("Trailing 12 Months"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download structured JSON executive report."""
    report = await report_service.generate_executive_report(db, period)
    return report
