
from io import BytesIO

from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet


def build_pdf_report(
    patient,
    assessment,
    narrative,
    record_id
):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "MediGuide AI - Patient Guidance Report",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "<b>IMPORTANT:</b> Educational information only. "
            "This is not a diagnosis, treatment plan, or substitute "
            "for qualified medical advice.",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"Session ID: {record_id}",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"Age: {escape(str(patient.get('age', '')))}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"Symptoms: {escape(str(patient.get('symptoms', '')))}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"Duration: {escape(str(patient.get('duration', '')))}",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Assessment Summary",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            escape(str(assessment.get("summary", ""))),
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "Suggested Urgency: "
            + escape(str(assessment.get("urgency_level", ""))),
            styles["Heading2"]
        )
    )

    sections = [

        ("Possible Conditions", "possible_conditions"),
        ("Recommended Next Steps", "recommended_next_steps"),
        ("Questions for Doctor", "questions_for_doctor"),
        ("Warning Signs", "warning_signs")

    ]

    for heading, key in sections:

        story.append(Spacer(1, 10))

        story.append(
            Paragraph(
                heading,
                styles["Heading2"]
            )
        )

        for item in assessment.get(key, []):

            if isinstance(item, dict):

                text = (
                    f"<b>{escape(str(item.get('name', '')))}</b>: "
                    f"{escape(str(item.get('reason', '')))}"
                )

            else:

                text = escape(str(item))

            story.append(
                Paragraph(
                    "• " + text,
                    styles["BodyText"]
                )
            )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Patient Guidance Explanation",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            escape(str(narrative)).replace("\n", "<br/>"),
            styles["BodyText"]
        )
    )

    document.build(story)

    return buffer.getvalue()
