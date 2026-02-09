from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
import uuid

from app.db.session import get_session
from app.models.jobs import NHSJob, UserJobAction, JobActionEnum
from app.services.auth import get_current_user
from app.services.dependencies import PaginationParams, pagination_params



class JobOut(BaseModel):
    id: uuid.UUID
    title: str
    date_posted: str
    salary: str
    contract: str
    reference_number: str
    address: str
    closing_date: str
    sponsored: bool
    link: str

    model_config = ConfigDict(from_attributes=True)

router = APIRouter()

def format_date(dt: date) -> str:
    if not dt:
        return ""
    return dt.strftime("%d %B %Y")  # e.g., "11 July 2025"


@router.get("/all", response_model=Dict[str, Any])
async def list_jobs(
    sponsored: Optional[bool] = Query(None, description="Filter by sponsorship"),
    sort: Optional[str] = Query("asc", pattern="^(asc|desc)$", description="Sort by closing date: 'asc' or 'desc'"),
    search: Optional[str] = Query(None, description="Search by job title"),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(pagination_params)
):
    # Get job_ids that the user has already taken action on
    user_actions_result = await db.execute(
        select(UserJobAction.job_id).where(UserJobAction.user_id == current_user.id)
    )
    excluded_job_ids = [row[0] for row in user_actions_result.all()]

    # Build base query for NHSJob
    base_query = select(NHSJob)
    if sponsored is not None:
        base_query = base_query.where(NHSJob.sponsored == sponsored)
    if excluded_job_ids:
        base_query = base_query.where(NHSJob.id.notin_(excluded_job_ids))
    if search:
        base_query = base_query.where(NHSJob.title.ilike(f"%{search}%"))

    # Filter jobs where closing_date is in the future (>= now)
    now = datetime.now()
    base_query = base_query.where(NHSJob.closing_date >= now)

    # Get total count before pagination
    count_result = await db.execute(base_query.with_only_columns(NHSJob.id))
    total = len(count_result.scalars().all())

    # Apply sorting and pagination
    query = base_query
    if sort == "asc":
        query = query.order_by(asc(NHSJob.closing_date))
    else:
        query = query.order_by(desc(NHSJob.closing_date))
    query = query.offset(pagination.skip).limit(pagination.limit)

    result = await db.execute(query)
    jobs = result.scalars().all()
    job_list = []
    for job in jobs:
        job_dict = job.__dict__.copy()
        job_dict["id"] = job.id  # keep as UUID, not str
        job_dict["date_posted"] = format_date(job.date_posted)
        job_dict["closing_date"] = format_date(job.closing_date)
        job_dict.pop("_sa_instance_state", None)
        job_list.append(JobOut(**job_dict))
    return {
        "total": total,
        "jobs": job_list
    }


@router.get("/user-jobs", response_model=List[JobOut])
async def list_user_jobs(
    action: JobActionEnum = Query(JobActionEnum.APPLIED, description="Filter by action: 'applied' or 'ignored'"),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
    pagination: PaginationParams = Depends(pagination_params)
):
    result = await db.execute(
        select(UserJobAction)
        .where(
            UserJobAction.user_id == current_user.id,
            UserJobAction.action == action
        )
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    actions = result.scalars().all()
    job_ids = [action.job_id for action in actions]
    if not job_ids:
        return []

    jobs_result = await db.execute(
        select(NHSJob).where(NHSJob.id.in_(job_ids))
    )
    jobs = jobs_result.scalars().all()
    job_list = []
    for job in jobs:
        job_dict = job.__dict__.copy()
        job_dict["id"] = job.id  # keep as UUID, not str
        job_dict["date_posted"] = format_date(job.date_posted)
        job_dict["closing_date"] = format_date(job.closing_date)
        job_dict.pop("_sa_instance_state", None)
        job_list.append(JobOut(**job_dict))
    return job_list


class UserJobActionIn(BaseModel):
    job_id: uuid.UUID
    action: JobActionEnum

@router.post("/user-jobs", status_code=201)
async def create_user_job_action(
    data: UserJobActionIn,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user)
):
    # Check if the action already exists for this user and job
    result = await db.execute(
        select(UserJobAction).where(
            UserJobAction.user_id == current_user.id,
            UserJobAction.job_id == data.job_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Action for this job already exists for the user."
        )
    user_job_action = UserJobAction(
        user_id=current_user.id,
        job_id=data.job_id,
        action=data.action
    )
    db.add(user_job_action)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id or user_id."
        )
    return {"message": "User job action created."}

@router.get("/jobs-count")
async def count_applied_jobs(
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user)
):
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Today
    result_today = await db.execute(
        select(UserJobAction)
        .where(
            UserJobAction.user_id == current_user.id,
            UserJobAction.action == JobActionEnum.APPLIED,
            UserJobAction.timestamp >= today_start
        )
    )
    count_today = len(result_today.scalars().all())

    # Last week (excluding today)
    result_week = await db.execute(
        select(UserJobAction)
        .where(
            UserJobAction.user_id == current_user.id,
            UserJobAction.action == JobActionEnum.APPLIED,
            UserJobAction.timestamp >= week_start,
            UserJobAction.timestamp < today_start
        )
    )
    count_week = len(result_week.scalars().all())

    # Last month (excluding this week and today)
    result_month = await db.execute(
        select(UserJobAction)
        .where(
            UserJobAction.user_id == current_user.id,
            UserJobAction.action == JobActionEnum.APPLIED,
            UserJobAction.timestamp >= month_start,
            UserJobAction.timestamp < week_start
        )
    )
    count_month = len(result_month.scalars().all())

    return {
        "applied_today": count_today,
        "applied_last_week": count_week,
        "applied_last_month": count_month
    }