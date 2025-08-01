"""
TechInsights  - Audit Log Model
Model for comprehensive audit trail of all data changes
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, text, JSON, ARRAY
)
from sqlalchemy.dialects.postgresql import INET
from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    pass


class AuditLog(Base):
    """Model for comprehensive audit trail for all data changes."""
    
    __tablename__ = "audit_log"
    
    # Primary key
    audit_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for audit record"
    )
    
    # Record identification
    table_name = Column(
        String(50),
        nullable=False,
        comment="Name of the table that was modified"
    )
    
    record_id = Column(
        Integer,
        nullable=False,
        comment="ID of the record that was modified"
    )
    
    operation = Column(
        String(10),
        nullable=False,
        comment="Type of operation (INSERT, UPDATE, DELETE)"
    )
    
    # Change details
    old_values = Column(
        JSON,
        comment="Previous values before the change"
    )
    
    new_values = Column(
        JSON,
        comment="New values after the change"
    )
    
    changed_fields = Column(
        ARRAY(String),
        comment="Array of field names that were changed"
    )
    
    # Change attribution
    changed_by = Column(
        String(100),
        comment="System user or process that made the change"
    )
    
    change_reason = Column(
        text,
        comment="Reason or description of why the change was made"
    )
    
    # Session and context information
    ip_address = Column(
        INET,
        comment="IP address of the client making the change"
    )
    
    user_agent = Column(
        text,
        comment="User agent string of the client"
    )
    
    session_id = Column(
        String(100),
        comment="Session identifier if applicable"
    )
    
    # Timestamp
    changed_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        comment="When the change was made"
    )
    
    def __repr__(self) -> str:
        """String representation of the AuditLog."""
        return (f"<AuditLog(table={self.table_name}, record_id={self.record_id}, "
                f"operation={self.operation}, changed_by={self.changed_by})>")

