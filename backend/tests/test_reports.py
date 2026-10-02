"""
Tests for executive report generation and export serialization.
"""

import pytest
from app.schemas.agent_schemas import ExecutiveReport
from app.services.report_service import report_service


class TestReportService:
    """Test report formatting, CSV export, and PDF bytes generation."""

    @pytest.fixture
    def sample_report(self) -> ExecutiveReport:
        return ExecutiveReport(
            title="Executive Operations & Analytics Report",
            period="Trailing 12 Months",
            generated_at="2025-10-24 12:00 UTC",
            executive_summary="Total revenue reached $142,580 with healthy operating margins.",
            revenue_performance="North America led regional contributions with 45% volume.",
            customer_performance="Total customers reached 620 with an average LTV of $77.49.",
            product_performance="Enterprise Cloud AI Suite generated $42,500 in sales.",
            expense_performance="Operating expenses remained steady with expense-to-revenue at 55.4%.",
            anomalies_summary="No critical operational variance detected.",
            key_insights=["Enterprise software is primary margin driver", "APAC growth velocity is strong"],
            identified_risks=["Regional concentration in North America"],
            investigation_recommendations=["Initiate proactive churn mitigation outreach"],
            supporting_metrics={"total_revenue": 142580.0, "total_expenses": 79000.0},
        )

    def test_export_report_csv(self, sample_report):
        csv_str = report_service.export_report_csv(sample_report)
        assert "AI BUSINESS OPERATIONS AGENT — EXECUTIVE REPORT" in csv_str
        assert "Trailing 12 Months" in csv_str
        assert "Enterprise software is primary margin driver" in csv_str
        assert "total_revenue" in csv_str

    def test_export_report_pdf_bytes(self, sample_report):
        pdf_bytes = report_service.export_report_pdf_bytes(sample_report)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 200
        # Valid PDF header or byte stream
        assert pdf_bytes.startswith(b"%PDF") or b"PDF" in pdf_bytes
