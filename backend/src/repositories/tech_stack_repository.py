"""
TechInsights  - Tech Stack Repository
Repository for technology stack database operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from typing import List, Optional, Dict, Any
import logging

from src.models.tech_stack import TechStack
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TechStackRepository(BaseRepository[TechStack]):
    """Repository for technology stack database operations."""
    
    def __init__(self, db: Session):
        super().__init__(TechStack, db)
    
    def get_by_normalized_name(self, normalized_name: str) -> Optional[TechStack]:
        """Get tech stack by normalized name."""
        return self.get_by_field("normalized_name", normalized_name)
    
    def search_technologies(self, search_term: str, limit: int = 20) -> List[TechStack]:
        """Search technologies by name or aliases."""
        try:
            stmt = (
                select(TechStack)
                .where(
                    or_(
                        TechStack.technology_name.ilike(f"%{search_term}%"),
                        TechStack.normalized_name.ilike(f"%{search_term}%"),
                        TechStack.aliases.op('@>')(f'{{"{search_term}"}}'::TEXT[])
                    )
                )
                .order_by(TechStack.popularity_score.desc())
                .limit(limit)
            )
            
            result = self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching technologies: {e}")
            raise
    
    def get_by_category(self, category: str) -> List[TechStack]:
        """Get technologies by category."""
        return self.get_multi(
            filters={"category": category},
            order_by="popularity_score",
            order_desc=True
        )
    
    def get_popular_technologies(self, limit: int = 50) -> List[TechStack]:
        """Get most popular technologies."""
        return self.get_multi(
            limit=limit,
            order_by="popularity_score",
            order_desc=True
        )

