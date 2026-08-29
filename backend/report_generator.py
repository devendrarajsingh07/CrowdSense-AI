import os
import tempfile
from datetime import datetime
from html import escape

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _line(label, value, style):
    return Paragraph(f"{escape(label)}: {escape(str(value))}", style)


def generate_report(data):
    descriptor, filename = tempfile.mkstemp(
        prefix="crowdsense-report-",
        suffix=".pdf",
    )
    os.close(descriptor)

    try:
        doc = SimpleDocTemplate(filename)
        styles = getSampleStyleSheet()
        normal = styles["Normal"]

        elements = [
            Paragraph("CrowdSense AI Report", styles["Title"]),
            Spacer(1, 12),
            _line("Generated", datetime.now().astimezone().isoformat(), normal),
            Spacer(1, 12),
            _line("Camera Status", data.get("camera", "UNKNOWN"), normal),
            _line("Current People Count", data.get("people", 0), normal),
            _line("Peak Crowd", data.get("peak", 0), normal),
            _line("Average Crowd", data.get("average", 0), normal),
            _line("Occupancy", f"{data.get('occupancy', 0)}%", normal),
            _line("High Risk Events", data.get("high_risk", 0), normal),
            _line("Database Records", data.get("db_records", 0), normal),
        ]

        doc.build(elements)
        return filename
    except Exception:
        try:
            os.unlink(filename)
        except FileNotFoundError:
            pass
        raise
