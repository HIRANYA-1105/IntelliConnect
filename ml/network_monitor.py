"""
Feature: proactive network issue detection.

Idea: instead of waiting for a customer to type "my internet is down", the
system watches how many independent reports have come in from the same
pincode/area in a short time window. Once that count crosses a threshold,
every customer in that area gets a proactive alert -- before they've said
anything. This is the ML/AI-adjacent "predictive" half of feature 1, kept
as a transparent rule over live report counts (a fine first version; a
real deployment might replace the fixed threshold with an anomaly-detection
model over historical report-rate baselines per area).
"""
from datetime import datetime, timedelta
from models import db, NetworkReport

REPORT_WINDOW_MINUTES = 60
ALERT_THRESHOLD = 3  # reports from an area within the window => likely outage


def log_report(pincode: str, issue_type: str = "outage"):
    report = NetworkReport(pincode=pincode, issue_type=issue_type)
    db.session.add(report)
    db.session.commit()
    return report


def check_area_status(pincode: str) -> dict:
    since = datetime.utcnow() - timedelta(minutes=REPORT_WINDOW_MINUTES)
    recent_reports = NetworkReport.query.filter(
        NetworkReport.pincode == pincode,
        NetworkReport.reported_at >= since,
    ).count()

    if recent_reports >= ALERT_THRESHOLD:
        return {
            "status": "likely_outage",
            "report_count": recent_reports,
            "message": (
                f"We're seeing {recent_reports} network reports from your area "
                f"(pincode {pincode}) in the last hour. Our team has already been "
                f"notified -- you don't need to file a separate complaint."
            ),
        }
    return {
        "status": "normal",
        "report_count": recent_reports,
        "message": None,
    }
