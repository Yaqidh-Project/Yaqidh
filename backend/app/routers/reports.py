import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
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

router = APIRouter(prefix="/reports", tags=["reports"])

ALLOWED_ROLES = ("Manager", "Parent")


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def generate_report(
    filters: ReportFilterCriteria,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    query = select(Incident)

    if current_user.role_name != "Manager":
        query = (
            query
            .join(Incident.camera)
            .join(Camera.zone)
            .join(Zone.users)
            .where(User.user_id == current_user.user_id)
        )

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

    summary_parts = [f"Total incidents: {len(incidents)}"]
    if incidents:
        categories: dict[str, int] = {}
        for inc in incidents:
            categories[inc.danger_category] = categories.get(inc.danger_category, 0) + 1
        for cat, count in categories.items():
            summary_parts.append(f"{cat}: {count}")
    summary = " | ".join(summary_parts)

    report = Report(
        filter_criteria=filters.model_dump(mode="json"),
        report_summary=summary,
        user_id=current_user.user_id,
        incidents=list(incidents),
    )
    db.add(report)
    await db.flush()

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
    query = (
        select(Report)
        .options(selectinload(Report.incidents))
        .where(Report.user_id == current_user.user_id)
        .order_by(Report.generated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if current_user.role_name == "Manager":
        query = (
            select(Report)
            .options(selectinload(Report.incidents))
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
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.incidents))
        .where(Report.report_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if current_user.role_name != "Manager" and report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to this report")
    return report


@router.get("/{report_id}/export", summary="Export report as JSON (download stub)")
async def export_report(
    report_id: uuid.UUID,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.incidents))
        .where(Report.report_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if current_user.role_name != "Manager" and report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied to this report")

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
                "detections": i.detections,
            }
            for i in report.incidents
        ],
    }
    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="report_{report.report_id}.json"',
            "Content-Type": "application/json",
        },
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    current_user: User = Depends(require_roles(*ALLOWED_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if current_user.role_name != "Manager" and report.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(report)
