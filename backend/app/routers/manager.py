"""
Manager-only operations:
- Create teachers and link them to a zone
- Monitor alert routing and performance tracking across zones
"""
import uuid
import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.zone import Zone
from app.models.incident import Incident
from app.schemas.user import TeacherCreate, UserOut
from app.schemas.manager import PerformanceDashboardOut, ZonePerformanceMetric
from app.auth.dependencies import require_roles

router = APIRouter(prefix="/manager", tags=["manager"])


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


@router.post(
    "/create-teacher",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Teacher account (Manager only)",
)
async def create_teacher(
    payload: TeacherCreate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    teacher = User(
        full_name=payload.full_name,
        email=payload.email,
        password=_hash_password(payload.password),
        phone_number=payload.phone_number,
        role_name="Teacher",
        notification_prefs=payload.notification_prefs,
        phone_verified=False,
    )
    db.add(teacher)
    await db.flush()
    await db.refresh(teacher)

    if payload.zone_id:
        zone_result = await db.execute(
            select(Zone)
            .options(selectinload(Zone.users))
            .where(Zone.zone_id == payload.zone_id)
        )
        zone = zone_result.scalar_one_or_none()
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")
        if teacher not in zone.users:
            zone.users.append(teacher)
        await db.flush()

    return teacher


@router.get(
    "/performance-dashboard",
    response_model=PerformanceDashboardOut,
    summary="Get performance and response times across all nursery zones (Manager only)",
)
async def get_performance_dashboard(
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    """
    Compiles real-time metrics for the manager dashboard, ISOLATED strictly
    to the logged-in manager's nursery data.
    """
    # FIX: Join the assigned_to table and filter strictly by the current manager's user_id
    zone_query = await db.execute(
        select(Zone)
        .join(Zone.users)
        .where(User.user_id == current_user.user_id)  # <-- THIS ENFORCES ABSOLUTE ISOLATION
        .options(
            selectinload(Zone.users), 
            selectinload(Zone.cameras)
        )
    )
    zones = zone_query.scalars().all()

    zones_performance = []
    total_nursery_incidents = 0
    total_nursery_resolved = 0
    total_nursery_response_time = 0.0

    for zone in zones:
        camera_ids = [cam.camera_id for cam in zone.cameras]
        # Renamed variable to teachers
        teachers = [user.full_name for user in zone.users if user.role_name == "Teacher"]
        
        if not camera_ids:
            zones_performance.append(
                ZonePerformanceMetric(
                    zone_id=zone.zone_id,
                    zone_name=zone.zone_name,
                    assigned_teachers=teachers,  # Updated parameter name
                    total_incidents=0,
                    resolved_incidents=0,
                    average_response_time_seconds=None
                )
            )
            continue
            
        incident_query = await db.execute(
            select(
                func.count(Incident.incident_id).label("total"),
                func.count(Incident.resolved_at).label("resolved"),
                func.sum(
                    extract("epoch", Incident.resolved_at) - extract("epoch", Incident.timestamp)
                ).label("total_time")
            ).where(Incident.camera_id.in_(camera_ids))
        )
        
        metrics = incident_query.tuples().one_or_none()
        
        total_incidents = 0
        resolved_incidents = 0
        total_time = 0.0
        
        if metrics:
            total_incidents = metrics[0] or 0
            resolved_incidents = metrics[1] or 0
            total_time = float(metrics[2]) if metrics[2] is not None else 0.0
            
        avg_time = None
        if resolved_incidents > 0:
            avg_time = round(total_time / resolved_incidents, 2)
            
            total_nursery_incidents += total_incidents
            total_nursery_resolved += resolved_incidents
            total_nursery_response_time += total_time

        zones_performance.append(
            ZonePerformanceMetric(
                zone_id=zone.zone_id,
                zone_name=zone.zone_name,
                assigned_teachers=teachers,  # Updated parameter name
                total_incidents=total_incidents,
                resolved_incidents=resolved_incidents,
                average_response_time_seconds=avg_time
            )
        )

    global_avg = None
    if total_nursery_resolved > 0:
        global_avg = round(total_nursery_response_time / total_nursery_resolved, 2)

    return {
        "summary": {
            "total_nursery_incidents": total_nursery_incidents,
            "total_nursery_resolved_incidents": total_nursery_resolved,
            "nursery_average_response_time_seconds": global_avg,
        },
        "zones_performance": zones_performance,
    }