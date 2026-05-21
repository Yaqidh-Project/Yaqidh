import json
import uuid
from io import BytesIO
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.report import Report
from app.models.incident import Incident
from app.models.camera import Camera
from app.models.zone import Zone
from app.models.user import User
from app.schemas.report import ReportOut, ReportFilterCriteria
from app.auth.dependencies import require_roles

# Import ReportLab modules for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

router = APIRouter(prefix="/reports", tags=["reports"])

# Teachers are strictly restricted; only Managers and Parents can access reports
ALLOWED_ROLES = ("Manager", "Parent")


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def generate_report(
    filters: ReportFilterCriteria,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a new report based on user role and specific filtering criteria,
    ensuring strict contextual isolation boundaries.
    """
    query = select(Incident)

    # Secure Multi-Tenancy Data Isolation bound matrix grid
    query = (
        query
        .join(Incident.camera)
        .join(Camera.zone)
        .join(Zone.users)
        .where(User.user_id == current_user.user_id)
    )

    # Apply additional dynamic filters passed from the frontend layout
    if filters.start_date:
        query = query.where(Incident.timestamp >= filters.start_date)
    if filters.end_date:
        query = query.where(Incident.timestamp <= filters.end_date)
    if filters.danger_category:
        query = query.where(Incident.danger_category == filters.danger_category.value)
    if filters.status:
        query = query.where(Incident.status == filters.status)
    if filters.camera_id:
        query = query.where(Incident.camera_id == filters.camera_id)

    result = await db.execute(query.order_by(Incident.timestamp.desc()))
    incidents = result.scalars().all()

    # Automatically generate a professional executive summary text block
    summary_parts = f"Total incidents captured: {len(incidents)}"
    if incidents:
        categories: dict[str, int] = {}
        for inc in incidents:
            categories[inc.danger_category] = categories.get(inc.danger_category, 0) + 1
        cat_details = " | ".join([f"{cat}: {count}" for cat, count in categories.items()])
        summary_parts += f" ({cat_details})"

    # Instantiate the report record by passing the M2M list during initialization.
    # This securely circumvents lazy loading / MissingGreenlet exceptions in Async sessions.
    report = Report(
        filter_criteria=filters.model_dump(mode="json"),
        report_summary=summary_parts,
        user_id=current_user.user_id,
        incidents=list(incidents),
    )
    db.add(report)
    await db.flush()
    
    # Securely commit transaction block block to disk storage
    await db.commit()

    # Eagerly reload full relational tree schema structure to safely match response schema model
    result2 = await db.execute(
        select(Report)
        .options(selectinload(Report.incidents))
        .where(Report.report_id == report.report_id)
    )
    return result2.scalar_one()


@router.get("", response_model=list[ReportOut])
async def list_reports(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves history of reports generated exclusively by the logged-in user session context.
    """
    query = (
        select(Report)
        .options(selectinload(Report.incidents))
        .where(Report.user_id == current_user.user_id)
        .order_by(Report.generated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches a single report details ensuring strict data ownership access control verification.
    """
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.incidents))
        .where(Report.report_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Guard Access Isolation Rules Block
    if report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to this report")
    return report


@router.get("/{report_id}/export-json", summary="Export report as JSON")
async def export_report_json(
    report_id: uuid.UUID,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """
    Exports report metadata and nested incident entries into a raw structured secure JSON payload download file.
    """
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.incidents))
        .where(Report.report_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to export this report")

    payload = {
        "report_id": str(report.report_id),
        "generated_at": report.generated_at.isoformat(),
        "filter_criteria": report.filter_criteria,
        "report_summary": report.report_summary,
        "incident_count": len(report.incidents),
        "incidents": [
            {
                "incident_id": str(i.incident_id),
                "timestamp": i.timestamp.isoformat(),
                "danger_category": i.danger_category,
                "incident_type": i.incident_type,
                "status": i.status,
                "confidence": i.confidence,
            }
            for i in report.incidents
        ],
    }
    
    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="Yaqidh_Report_{report.report_id}.json"',
            "Content-Type": "application/json",
        },
    )


@router.get("/{report_id}/export-pdf", summary="Export report as PDF document")
async def export_report_pdf(
    report_id: uuid.UUID,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """
    Dynamically constructs a formatted PDF safety document stream structure using ReportLab framework flowables.
    """
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.incidents))
        .where(Report.report_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to export this report")

    # In-memory binary stream structure setup for performance efficiency
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    # Config Document Document Style Elements Layout Sheet
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'PDFTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor("#1A365D"), spaceAfter=12
    )
    meta_style = ParagraphStyle(
        'PDFMeta', parent=styles['Normal'], fontSize=10, textColor=colors.gray, spaceAfter=6
    )
    summary_style = ParagraphStyle(
        'PDFSummary', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor("#2C3E50"), backColor=colors.HexColor("#ECF0F1"), borderPadding=10, spaceAfter=20
    )
    table_text_style = ParagraphStyle('TableText', parent=styles['Normal'], fontSize=9)

    # Appending UI Node Flowables Elements Elements
    story.append(Paragraph("YAQIDH SYSTEM - INCIDENT SAFETY REPORT", title_style))
    story.append(Paragraph(f"<b>Report ID:</b> {report.report_id}", meta_style))
    story.append(Paragraph(f"<b>Generated On:</b> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
    story.append(Paragraph(f"<b>Account Holder ID:</b> {report.user_id} ({current_user.role_name} Environment)", meta_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(f"<b>Executive Summary:</b> {report.report_summary}", summary_style))
    story.append(Paragraph("Detailed Incidents Log:", styles['Heading2']))
    story.append(Spacer(1, 8))

    # Compile the layout framework data matrix structure grid
    table_data = [["Timestamp", "Danger Category", "Incident Type", "Confidence"]]
    
    for inc in report.incidents:
        time_str = inc.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        table_data.append([
            Paragraph(time_str, table_text_style),
            Paragraph(str(inc.danger_category), table_text_style),
            Paragraph(str(inc.incident_type), table_text_style),
            Paragraph(f"{inc.confidence * 100:.1f}%", table_text_style)
        ])

    # Assign dynamic grid columns matching standard layout margins bounds (Total 500 Width units)
    incidents_table = Table(table_data, colWidths=[125, 125, 150, 100])
    incidents_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(incidents_table)
    
    # Process compilation layout stream block context
    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Yaqidh_Safety_Report_{report.report_id}.pdf"'
        }
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a specific archived report record from the persistence database storage cluster.
    """
    result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    await db.delete(report)
    await db.commit()