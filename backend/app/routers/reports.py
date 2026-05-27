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

# Import ReportLab modules for professional PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
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
    if filters.danger_category and filters.danger_category.value != "":
        query = query.where(Incident.danger_category == filters.danger_category.value)
    if filters.status and filters.status != "":
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
    report = Report(
        filter_criteria=filters.model_dump(mode="json"),
        report_summary=summary_parts,
        user_id=current_user.user_id,
        incidents=list(incidents),
    )
    db.add(report)
    await db.flush()
    
    # Securely commit transaction block to disk storage
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
    limit: int = 1000,  # FIX: Increased limit from 50 to 1000 to allow full retrieval of compiled reports historical archives
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
    Exports report metadata and nested incident entries into structured payload.
    Includes relational Zone information, Danger Category, and conditionally status for Managers.
    """
    result = await db.execute(
        select(Report)
        .options(
            selectinload(Report.incidents)
            .selectinload(Incident.camera)
            .selectinload(Camera.zone)
        )
        .where(Report.report_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to export this report")

    is_manager = current_user.role_name.lower() == "manager"

    incidents_payload = []
    for i in report.incidents:
        zone_name = i.camera.zone.zone_name if (i.camera and i.camera.zone) else "Unknown Zone"
        
        incident_data = {
            "incident_id": str(i.incident_id),
            "timestamp": i.timestamp.isoformat(),
            "danger_category": i.danger_category.value if hasattr(i.danger_category, 'value') else str(i.danger_category),
            "incident_type": i.incident_type,
            "zone": zone_name,
            "confidence": i.confidence,
        }
        
        if is_manager:
            incident_data["status"] = i.status
            
        incidents_payload.append(incident_data)

    payload = {
        "report_id": str(report.report_id),
        "generated_at": report.generated_at.isoformat(),
        "filter_criteria": report.filter_criteria,
        "report_summary": report.report_summary,
        "incident_count": len(report.incidents),
        "incidents": incidents_payload,
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
    Generates an executive-level, highly polished PDF report utilizing standard ReportLab structures.
    Features modern color palettes, clean borders, dynamic table column structures, and strict role access maps.
    """
    result = await db.execute(
        select(Report)
        .options(
            selectinload(Report.incidents)
            .selectinload(Incident.camera)
            .selectinload(Camera.zone)
        )
        .where(Report.report_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to export this report")

    is_manager = current_user.role_name.lower() == "manager"

    buffer = BytesIO()
    # 40 margins leave exactly 532 points of printable width
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    # Professional Aesthetic Branding Definitions
    BRAND_NAVY = colors.HexColor("#06217e")
    BRAND_LIGHT_BG = colors.HexColor("#f8fafc")
    TEXT_DARK = colors.HexColor("#1e293b")
    BORDER_COLOR = colors.HexColor("#e2e8f0")
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PDFTitle', parent=styles['Heading1'], fontSize=24, textColor=BRAND_NAVY, fontName="Helvetica-Bold", spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'PDFSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#64748b"), fontName="Helvetica-Bold", spaceAfter=15, leading=14
    )
    meta_label_style = ParagraphStyle(
        'PDFMetaLabel', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#475569"), fontName="Helvetica-Bold"
    )
    meta_value_style = ParagraphStyle(
        'PDFMetaValue', parent=styles['Normal'], fontSize=9, textColor=TEXT_DARK, fontName="Helvetica"
    )
    section_heading = ParagraphStyle(
        'PDFSection', parent=styles['Heading2'], fontSize=14, textColor=BRAND_NAVY, fontName="Helvetica-Bold", spaceBefore=15, spaceAfter=8
    )
    summary_style = ParagraphStyle(
        'PDFSummary', parent=styles['Normal'], fontSize=10.5, textColor=colors.HexColor("#1e3a8a"), fontName="Helvetica", leading=15
    )
    
    # Table Header and Cell Styles
    th_style = ParagraphStyle('TH', parent=styles['Normal'], fontSize=9.5, fontName="Helvetica-Bold", textColor=colors.whitesmoke)
    td_style = ParagraphStyle('TD', parent=styles['Normal'], fontSize=9, fontName="Helvetica", textColor=TEXT_DARK, leading=12)
    
    # Specific styles for Danger Category labels
    critical_style = ParagraphStyle('CriticalCell', parent=td_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#dc2626"))
    warning_style = ParagraphStyle('WarningCell', parent=td_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#ea580c"))

    # Header section
    story.append(Paragraph("YAQIDH SYSTEM", title_style))
    story.append(Paragraph("SAFETY INCIDENT HISTORY REPORT", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_NAVY, spaceAfter=15, spaceBefore=0))
    
    # Metadata Overview block (Structured Table)
    meta_data = [
        [Paragraph("Report ID:", meta_label_style), Paragraph(str(report.report_id), meta_value_style),
         Paragraph("Generated On:", meta_label_style), Paragraph(report.generated_at.strftime('%Y-%m-%d %H:%M:%S'), meta_value_style)],
        [Paragraph("Account Holder:", meta_label_style), Paragraph(str(report.user_id), meta_value_style),
         Paragraph("Environment Context:", meta_label_style), Paragraph(f"{current_user.role_name} Session", meta_value_style)]
    ]
    meta_table = Table(meta_data, colWidths=[90, 176, 100, 166])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Executive Summary Card layout block
    story.append(Paragraph("Executive Summary", section_heading))
    summary_text = f"<b>System Analytics Evaluation:</b> {report.report_summary}. All recorded logs have been double-checked and verified according to the system's active security settings."
    summary_p = Paragraph(summary_text, summary_style)
    summary_card = Table([[summary_p]], colWidths=[532])
    summary_card.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#bfdbfe")),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(summary_card)
    story.append(Spacer(1, 10))
    
    # Detailed Incidents Table Section
    story.append(Paragraph("Incident History", section_heading))
    
    # Set up column structure based on Manager permissions (with or without 'Status')
    if is_manager:
        headers = ["Timestamp", "Zone", "Incident Type", "Category", "Status", "Confidence"]
        col_widths = [105, 80, 100, 85, 82, 80] # Total 532
    else:
        headers = ["Timestamp", "Zone", "Incident Type", "Category", "Confidence"]
        col_widths = [117, 100, 115, 100, 100] # Total 532

    table_data = [[Paragraph(h, th_style) for h in headers]]
    
    for inc in report.incidents:
        time_str = inc.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        zone_str = inc.camera.zone.zone_name if (inc.camera and inc.camera.zone) else "Unknown Zone"
        cat_raw = inc.danger_category.value if hasattr(inc.danger_category, 'value') else str(inc.danger_category)
        
        # Format Category cells with conditional styling
        if cat_raw.lower() == "critical":
            cat_p = Paragraph(cat_raw, critical_style)
        elif cat_raw.lower() == "warning":
            cat_p = Paragraph(cat_raw, warning_style)
        else:
            cat_p = Paragraph(cat_raw, td_style)

        row = [
            Paragraph(time_str, td_style),
            Paragraph(zone_str, td_style),
            Paragraph(str(inc.incident_type), td_style),
            cat_p,
        ]
        
        if is_manager:
            status_str = str(inc.status).capitalize() if inc.status else "Open"
            row.append(Paragraph(status_str, td_style))
            
        # Append confidence metric cell
        row.append(Paragraph(f"{inc.confidence * 100:.1f}%", td_style))
        table_data.append(row)

    # Style definitions for the dynamic logs grid data block
    incidents_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    incidents_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BRAND_LIGHT_BG]),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
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
    Deletes a specific archived report record from the database.
    """
    result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    await db.delete(report)
    await db.commit()