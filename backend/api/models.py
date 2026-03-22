from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class EnrollmentStatus(str, Enum):
    enrolled = "enrolled"
    leave_of_absence = "leave_of_absence"
    graduated = "graduated"


class GradeLevel(str, Enum):
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    graduate = "graduate"
    other = "other"


INFO_FOCUS_VALUES = {"spec_building", "campus_info", "job", "hackathon", "competition", "scholarship"}


class UserCreate(BaseModel):
    email: str
    name: str | None = None
    school: str
    major: str
    enrollment_status: EnrollmentStatus
    grade: GradeLevel
    info_focus: list[str] = []
    bio: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    school: str | None = None
    major: str | None = None
    enrollment_status: EnrollmentStatus | None = None
    grade: GradeLevel | None = None
    info_focus: list[str] | None = None
    bio: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    school: str
    major: str
    enrollment_status: str
    grade: str
    info_focus: list[str]
    bio: str | None
    created_at: datetime
