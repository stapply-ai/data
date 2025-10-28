import pydantic
from datetime import datetime
from typing import Optional
from uuid import UUID


class Company(pydantic.BaseModel):
    id: Optional[UUID] = None
    name: str


class DatabaseJob(pydantic.BaseModel):
    id: Optional[UUID] = None
    url: str
    title: str
    location: Optional[str] = None
    company: str
    description: Optional[str] = None
    employment_type: Optional[str] = None
    industry: Optional[str] = None
    embedding: Optional[str] = None  # vector type
    posted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    source: Optional[str] = None
    is_active: bool = True
    added_by_user: Optional[bool] = False
    remote: Optional[bool] = None
    wfh: Optional[bool] = None
    application_url: Optional[str] = None
    language: Optional[str] = None
    title_embedding: Optional[str] = None  # vector type
    verified_at: Optional[datetime] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    country: Optional[str] = None
    point: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    city: Optional[str] = None
    ats_type: Optional[str] = None
    company_id: Optional[UUID] = None
