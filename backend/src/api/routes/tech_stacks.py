"""
StackRadar  - Tech Stacks API Routes
Technology stack management endpoints
"""

from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter()


class TechStackResponse(BaseModel):
    """Technology stack response model."""
    tech_id: int
    name: str
    category: str
    popularity_score: float


@router.get("/", response_model=List[TechStackResponse])
async def list_tech_stacks():
    """List all technology stacks."""
    return [
        TechStackResponse(
            tech_id=1,
            name="React",
            category="Frontend",
            popularity_score=85.2
        ),
        TechStackResponse(
            tech_id=2,
            name="Python",
            category="Backend",
            popularity_score=92.1
        )
    ]