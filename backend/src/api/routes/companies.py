"""
StackRadar  - Companies API Routes
Company profiles and analytics endpoints
"""

from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter()


class CompanyResponse(BaseModel):
    """Company response model."""
    company_id: int
    name: str
    industry: str
    size: str
    job_count: int


@router.get("/", response_model=List[CompanyResponse])
async def list_companies():
    """List companies with job postings."""
    return [
        CompanyResponse(
            company_id=1,
            name="Tech Company NZ",
            industry="Technology",
            size="Medium",
            job_count=15
        ),
        CompanyResponse(
            company_id=2,
            name="Startup Ltd",
            industry="Software",
            size="Small",
            job_count=8
        )
    ]