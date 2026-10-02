"""
Tests for explainable statistical anomaly detection.
"""

import pytest
from app.services.anomaly_service import compute_z_score_anomalies


class TestAnomalyDetection:
    """Test statistical Z-score and percentage anomaly detection."""

    def test_stable_series_has_no_anomalies(self):
        series = [
            {"month": "2025-01", "val": 100},
            {"month": "2025-02", "val": 102},
            {"month": "2025-03", "val": 99},
            {"month": "2025-04", "val": 101},
            {"month": "2025-05", "val": 100},
            {"month": "2025-06", "val": 103},
        ]
        anomalies = compute_z_score_anomalies(
            series=series,
            val_key="val",
            date_key="month",
            metric_name="Monthly Metric",
            z_threshold=2.0,
            pct_threshold=0.25,
        )
        assert len(anomalies) == 0

    def test_sharp_drop_triggers_anomaly(self):
        series = [
            {"month": "2025-01", "revenue": 50000},
            {"month": "2025-02", "revenue": 51000},
            {"month": "2025-03", "revenue": 49500},
            {"month": "2025-04", "revenue": 52000},
            {"month": "2025-05", "revenue": 50500},
            {"month": "2025-06", "revenue": 18000},  # Severe drop ~64%
        ]
        anomalies = compute_z_score_anomalies(
            series=series,
            val_key="revenue",
            date_key="month",
            metric_name="Monthly Revenue",
            unit_prefix="$",
            z_threshold=1.75,
            pct_threshold=0.22,
        )
        assert len(anomalies) >= 1
        anom = anomalies[0]
        assert anom.period == "2025-06"
        assert anom.actual_value == 18000
        assert anom.z_score < -1.5
        assert "Monthly Revenue exhibited an unusual drop" in anom.explanation

    def test_sharp_spike_triggers_anomaly(self):
        series = [
            {"month": "2025-01", "expense": 10000},
            {"month": "2025-02", "expense": 10200},
            {"month": "2025-03", "expense": 9800},
            {"month": "2025-04", "expense": 10100},
            {"month": "2025-05", "expense": 24000},  # Spike ~140%
        ]
        anomalies = compute_z_score_anomalies(
            series=series,
            val_key="expense",
            date_key="month",
            metric_name="Operating Expenses",
            unit_prefix="$",
            z_threshold=1.75,
            pct_threshold=0.22,
        )
        assert len(anomalies) >= 1
        anom = anomalies[0]
        assert anom.period == "2025-05"
        assert anom.z_score > 1.5
        assert "spike" in anom.explanation
