"""
TechInsights  - Base Model
Base SQLAlchemy model with common fields and functionality
"""

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from typing import Any


class CustomBase:
    """Base model class with common fields and functionality."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.key: getattr(self, column.key)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


Base = declarative_base(cls=CustomBase)


class TimestampMixin:
    """Mixin for models that need created_at and updated_at timestamps."""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )


class IDMixin:
    """Mixin for models that need a primary key ID."""
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key identifier"
    )

