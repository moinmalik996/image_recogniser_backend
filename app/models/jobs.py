import uuid
from datetime import date, datetime
from enum import Enum
from sqlmodel import Field, Relationship
from .base import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User

class JobActionEnum(str, Enum):
    APPLIED = "applied"
    IGNORED = "ignored"

class NHSJob(BaseModel, table=True):
    __tablename__ = 'nhs_jobs'
    title: str
    date_posted: date
    salary: str
    contract: str
    reference_number: str
    address: str
    closing_date: date
    sponsored: bool
    link: str
    is_closed: bool = False

    user_actions: list["UserJobAction"] = Relationship(back_populates="job")

    model_config = {
        "arbitrary_types_allowed": True
    }


class UserJobAction(BaseModel, table=True):
    __tablename__ = 'user_job_actions'
    user_id: uuid.UUID = Field(foreign_key="user.id")
    job_id: uuid.UUID = Field(foreign_key="nhs_jobs.id")
    action: JobActionEnum
    timestamp: datetime = Field(default_factory=datetime.now)

    user: "User" = Relationship(back_populates="job_actions")
    job: NHSJob = Relationship(back_populates="user_actions")

    model_config = {
        "arbitrary_types_allowed": True
    }

# If not already present, add this to your User model:
# job_actions: list["UserJobAction"] = Relationship(back_populates="user")