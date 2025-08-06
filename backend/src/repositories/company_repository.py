"""
TechInsights  - Company Repository
Repository for company-related database operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
import logging

from src.models.company import Company
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CompanyRepository(BaseRepository[Company]):
    """Repository for company-related database operations."""
    
    def __init__(self, db: Session):
        super().__init__(Company, db)
    
    def get_by_normalized_name(self, normalized_name: str) -> Optional[Company]:
        """
        Get company by normalized name.
        
        Args:
            normalized_name: Normalized company name
            
        Returns:
            Optional[Company]: Company if found
        """
        return self.get_by_field("normalized_name", normalized_name)
    
    def search_by_name(self, name_query: str, limit: int = 20) -> List[Company]:
        """
        Search companies by name (fuzzy matching).
        
        Args:
            name_query: Search query
            limit: Maximum number of results
            
        Returns:
            List[Company]: Matching companies
        """
        try:
            stmt = (
                select(Company)
                .where(
                    Company.company_name.ilike(f"%{name_query}%")
                    | Company.normalized_name.ilike(f"%{name_query}%")
                )
                .order_by(Company.company_name)
                .limit(limit)
            )
            
            result = self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching companies by name '{name_query}': {e}")
            raise
    
    def get_companies_by_size(self, company_size: str) -> List[Company]:
        """
        Get companies filtered by size.
        
        Args:
            company_size: Company size category
            
        Returns:
            List[Company]: Companies of specified size
        """
        return self.get_multi(filters={"company_size": company_size})
    
    def get_companies_by_industry(self, industry: str) -> List[Company]:
        """
        Get companies filtered by industry.
        
        Args:
            industry: Industry name
            
        Returns:
            List[Company]: Companies in specified industry
        """
        return self.get_multi(filters={"industry": industry})
    
    def find_or_create_company(self, company_data: Dict[str, Any]) -> Company:
        """
        Find existing company or create new one.
        
        Args:
            company_data: Company information
            
        Returns:
            Company: Found or created company
        """
        try:
            # Normalize the company name
            from src.utils.text_processing import normalize_company_name
            
            company_name = company_data.get("company_name", "").strip()
            if not company_name:
                raise ValueError("Company name is required")
            
            normalized_name = normalize_company_name(company_name)
            
            # Try to find existing company
            existing_company = self.get_by_normalized_name(normalized_name)
            if existing_company:
                logger.debug(f"Found existing company: {existing_company.company_name}")
                return existing_company
            
            # Create new company
            company_data["normalized_name"] = normalized_name
            new_company = self.create(company_data)
            
            logger.info(f"Created new company: {new_company.company_name}")
            return new_company
            
        except Exception as e:
            logger.error(f"Error finding or creating company: {e}")
            raise

