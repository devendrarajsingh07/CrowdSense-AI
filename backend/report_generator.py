from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

from datetime import datetime

def generate_report(data):

    filename = "Crowd_Report.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "CrowdSense AI Report",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1,12)
    )

    elements.append(
        Paragraph(
            f"Generated: {datetime.now()}",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1,12)
    )

    elements.append(
        Paragraph(
            f"Current People Count: {data['people']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Peak Crowd: {data['peak']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Average Crowd: {data['average']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Occupancy: {data['occupancy']}%",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"High Risk Events: {data['high_risk']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Database Records: {data['db_records']}",
            styles["Normal"]
        )
    )

    doc.build(elements)

    return filename