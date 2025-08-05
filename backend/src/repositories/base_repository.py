"""
TechInsights  - Base Repository
Base repository class with common CRUD operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError, NoResultFound
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod
import logging

from src.models.base import Base

logger = logging.getLogger(__name__)

# Type variable for model classes
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType], ABC):
    """
    Base repository class providing common CRUD operations.
    
    This class implements the Repository pattern to provide a clean abstraction
    layer over database operations.
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model class and database session.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db
    
    # ========================================================================
    # CREATE OPERATIONS
    # ========================================================================
    
    def create(self, obj_in: Union[Dict[str, Any], CreateSchemaType]) -> ModelType:
        """
        Create a new record in the database.
        
        Args:
            obj_in: Data for creating the record (dict or Pydantic model)
            
        Returns:
            ModelType: Created model instance
            
        Raises:
            IntegrityError: If there are constraint violations
        """
        try:
            if hasattr(obj_in, 'dict'):
                # Pydantic model
                obj_data = obj_in.dict(exclude_unset=True)
            else:
                # Dictionary
                obj_data = obj_in
            
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            
            logger.debug(f"Created {self.model.__name__} with ID: {getattr(db_obj, 'id', 'N/A')}")
            return db_obj
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def create_batch(self, objects_in: List[Union[Dict[str, Any], CreateSchemaType]]) -> List[ModelType]:
        """
        Create multiple records in a single transaction.
        
        Args:
            objects_in: List of data for creating records
            
        Returns:
            List[ModelType]: List of created model instances
        """
        try:
            db_objects = []
            for obj_in in objects_in:
                if hasattr(obj_in, 'dict'):
                    obj_data = obj_in.dict(exclude_unset=True)
                else:
                    obj_data = obj_in
                
                db_obj = self.model(**obj_data)
                db_objects.append(db_obj)
                self.db.add(db_obj)
            
            self.db.commit()
            
            # Refresh all objects to get generated IDs
            for db_obj in db_objects:
                self.db.refresh(db_obj)
            
            logger.debug(f"Created {len(db_objects)} {self.model.__name__} records")
            return db_objects
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating batch {self.model.__name__}: {e}")
            raise
    
    # ========================================================================
    # READ OPERATIONS
    # ========================================================================
    
    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        """
        Get a record by its primary key ID.
        
        Args:
            record_id: Primary key value
            
        Returns:
            Optional[ModelType]: Model instance if found, None otherwise
        """
        try:
            stmt = select(self.model).where(self.model.id == record_id)
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by ID {record_id}: {e}")
            raise
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """
        Get a record by a specific field value.
        
        Args:
            field_name: Name of the field to search by
            value: Value to search for
            
        Returns:
            Optional[ModelType]: Model instance if found, None otherwise
        """
        try:
            field = getattr(self.model, field_name)
            stmt = select(self.model).where(field == value)
            result = self.db.execute(stmt)
            return result.scalar_one_or_none()
        except AttributeError:
            logger.error(f"Field {field_name} not found in {self.model.__name__}")
            raise
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by {field_name}: {e}")
            raise
    
    def get_multi(
        self, 
        offset: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.
        
        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: Whether to order in descending order
            
        Returns:
            List[ModelType]: List of model instances
        """
        try:
            stmt = select(self.model)
            
            # Apply filters
            if filters:
                conditions = []
                for field_name, value in filters.items():
                    if hasattr(self.model, field_name):
                        field = getattr(self.model, field_name)
                        if isinstance(value, list):
                            conditions.append(field.in_(value))
                        elif isinstance(value, tuple) and len(value) == 2:
                            # Range filter (min, max)
                            conditions.append(and_(field >= value[0], field <= value[1]))
                        else:
                            conditions.append(field == value)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if order_desc:
                    stmt = stmt.order_by(order_field.desc())
                else:
                    stmt = stmt.order_by(order_field)
            
            # Apply pagination
            stmt = stmt.offset(offset).limit(limit)
            
            result = self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            filters: Dictionary of field:value filters
            
        Returns:
            int: Number of matching records
        """
        try:
            stmt = select(func.count(self.model.id))
            
            # Apply filters
            if filters:
                conditions = []
                for field_name, value in filters.items():
                    if hasattr(self.model, field_name):
                        field = getattr(self.model, field_name)
                        if isinstance(value, list):
                            conditions.append(field.in_(value))
                        else:
                            conditions.append(field == value)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = self.db.execute(stmt)
            return result.scalar()
            
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise
    
    def exists(self, **kwargs) -> bool:
        """
        Check if a record exists with the given criteria.
        
        Args:
            **kwargs: Field:value pairs to check
            
        Returns:
            bool: True if record exists, False otherwise
        """
        try:
            conditions = []
            for field_name, value in kwargs.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    conditions.append(field == value)
            
            if not conditions:
                return False
            
            stmt = select(func.count(self.model.id)).where(and_(*conditions))
            result = self.db.execute(stmt)
            return result.scalar() > 0
            
        except Exception as e:
            logger.error(f"Error checking existence in {self.model.__name__}: {e}")
            raise
    
    # ========================================================================
    # UPDATE OPERATIONS
    # ========================================================================
    
    def update(
        self, 
        record_id: int, 
        obj_in: Union[Dict[str, Any], UpdateSchemaType]
    ) -> Optional[ModelType]:
        """
        Update a record by ID.
        
        Args:
            record_id: Primary key of record to update
            obj_in: Updated data (dict or Pydantic model)
            
        Returns:
            Optional[ModelType]: Updated model instance if found, None otherwise
        """
        try:
            # Get existing record
            db_obj = self.get_by_id(record_id)
            if not db_obj:
                return None
            
            # Prepare update data
            if hasattr(obj_in, 'dict'):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in
            
            # Apply updates
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            
            logger.debug(f"Updated {self.model.__name__} with ID: {record_id}")
            return db_obj
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__} {record_id}: {e}")
            raise
    
    def update_by_field(
        self, 
        field_name: str, 
        field_value: Any, 
        updates: Dict[str, Any]
    ) -> int:
        """
        Update records by field value.
        
        Args:
            field_name: Name of field to match
            field_value: Value to match
            updates: Dictionary of field:value updates
            
        Returns:
            int: Number of records updated
        """
        try:
            field = getattr(self.model, field_name)
            stmt = (
                update(self.model)
                .where(field == field_value)
                .values(**updates)
            )
            
            result = self.db.execute(stmt)
            self.db.commit()
            
            rows_updated = result.rowcount
            logger.debug(f"Updated {rows_updated} {self.model.__name__} records")
            return rows_updated
            
        except AttributeError:
            logger.error(f"Field {field_name} not found in {self.model.__name__}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk updating {self.model.__name__}: {e}")
            raise
    
    # ========================================================================
    # DELETE OPERATIONS
    # ========================================================================
    
    def delete(self, record_id: int) -> bool:
        """
        Delete a record by ID.
        
        Args:
            record_id: Primary key of record to delete
            
        Returns:
            bool: True if record was deleted, False if not found
        """
        try:
            db_obj = self.get_by_id(record_id)
            if not db_obj:
                return False
            
            self.db.delete(db_obj)
            self.db.commit()
            
            logger.debug(f"Deleted {self.model.__name__} with ID: {record_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__} {record_id}: {e}")
            raise
    
    def delete_by_field(self, field_name: str, field_value: Any) -> int:
        """
        Delete records by field value.
        
        Args:
            field_name: Name of field to match
            field_value: Value to match
            
        Returns:
            int: Number of records deleted
        """
        try:
            field = getattr(self.model, field_name)
            stmt = delete(self.model).where(field == field_value)
            
            result = self.db.execute(stmt)
            self.db.commit()
            
            rows_deleted = result.rowcount
            logger.debug(f"Deleted {rows_deleted} {self.model.__name__} records")
            return rows_deleted
            
        except AttributeError:
            logger.error(f"Field {field_name} not found in {self.model.__name__}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk deleting {self.model.__name__}: {e}")
            raise
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def refresh(self, db_obj: ModelType) -> ModelType:
        """
        Refresh a model instance from the database.
        
        Args:
            db_obj: Model instance to refresh
            
        Returns:
            ModelType: Refreshed model instance
        """
        self.db.refresh(db_obj)
        return db_obj
    
    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error committing transaction: {e}")
            raise
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()

