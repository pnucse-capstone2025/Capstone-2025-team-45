from datetime import datetime
from sqlalchemy import Column, BigInteger,  String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID  
from model.database import Base

class FunctionalUnits(Base):
    __tablename__ = 'functional_units'
    functional_unit_id = Column(
        BigInteger,               
        primary_key=True,         
        autoincrement=True        
    )
    functional_unit_name = Column(String(50), unique=True, index=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.organization_id'), nullable=False)

    # Relationships
    organization = relationship("Organizations", back_populates="functional_units")
    department = relationship("Departments", back_populates="functional_unit")
