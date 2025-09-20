from sqlalchemy import Column, BigInteger,  String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID  
from model.database import Base

class Teams(Base):
    __tablename__ = 'teams'
    team_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    team_name = Column(String(50), unique=True, index=True, nullable=False)
    department_id = Column(BigInteger,  ForeignKey('departments.department_id'), nullable=False)

    # Relationships
    department = relationship("Departments", back_populates="teams")
    employee = relationship("Employees", back_populates="team")