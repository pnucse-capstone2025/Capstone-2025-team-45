import uuid

from datetime import datetime

from sqlalchemy import Column, BigInteger,  String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID  
from model.database import Base

class Security_managers(Base):
    __tablename__ = 'security_managers'
    manager_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manager_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.organization_id'), nullable=False)

    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, default=None)

    # Relationships
    # Add any relationships if needed
    organization = relationship("Organizations", back_populates="security_managers")