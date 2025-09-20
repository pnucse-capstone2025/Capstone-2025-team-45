from sqlalchemy import Column, BigInteger,  String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID  
from model.database import Base

class Departments(Base):
    __tablename__ = 'departments'
    department_id = Column(
        BigInteger,               
        primary_key=True,         
        autoincrement=True        
    )
    department_name = Column(String(50), unique=True, index=True, nullable=False)
    functional_unit_id = Column(BigInteger,  ForeignKey('functional_units.functional_unit_id'), nullable=False)

    # Relationships
    functional_unit = relationship("FunctionalUnits", back_populates="department")
    teams = relationship("Teams", back_populates="department")