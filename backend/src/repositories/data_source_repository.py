"""
TechInsights  - Data Source Repository
Repository for data source management operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.models.data_source import DataSource
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DataSourceRepository(BaseRepository[DataSource]):
    """Repository for data source management operations."""
    
    def __init__(self, db: Session):
        super().__init__(DataSource, db)
    
    def get_by_name(self, source_name: str) -> Optional[DataSource]:
        """
        Get data source by name.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Optional[DataSource]: Data source if found
        """
        return self.get_by_field("source_name", source_name)
    
    def get_active_sources(self) -> List[DataSource]:
        """
        Get all active data sources.
        
        Returns:
            List[DataSource]: List of active data sources
        """
        return self.get_multi(filters={"is_active": True})
    
    def update_last_scraped(self, source_id: int) -> bool:
        """
        Update the last scraped timestamp for a data source.
        
        Args:
            source_id: Data source ID
            
        Returns:
            bool: True if updated successfully
        """
        try:
            updated = self.update(source_id, {"last_scraped_at": datetime.now()})
            return updated is not None
        except Exception as e:
            logger.error(f"Error updating last scraped for source {source_id}: {e}")
            return False
    
    def update_statistics(
        self,
        source_id: int,
        jobs_collected: int,
        success_count: int,
        total_attempts: int
    ) -> bool:
        """
        Update collection statistics for a data source.
        
        Args:
            source_id: Data source ID
            jobs_collected: Number of jobs collected
            success_count: Number of successful operations
            total_attempts: Total number of attempts
            
        Returns:
            bool: True if updated successfully
        """
        try:
            success_rate = (success_count / total_attempts * 100) if total_attempts > 0 else 0
            
            data_source = self.get_by_id(source_id)
            if not data_source:
                return False
            
            # Update statistics
            new_total = data_source.total_jobs_collected + jobs_collected
            
            updated = self.update(source_id, {
                "total_jobs_collected": new_total,
                "success_rate": success_rate,
                "last_scraped_at": datetime.now()
            })
            
            return updated is not None
            
        except Exception as e:
            logger.error(f"Error updating statistics for source {source_id}: {e}")
            return False

