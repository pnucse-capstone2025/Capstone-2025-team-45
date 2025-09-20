from sqlalchemy import Column, BigInteger,  String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID  
from model.database import Base

class Employees(Base):
    __tablename__ = 'employees'
    employee_id = Column(
        String(20),
        primary_key=True,
    )
    employee_name = Column(String(50), unique=True, index=True, nullable=False)
    team_id = Column(BigInteger,  ForeignKey('teams.team_id'), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False)
    supervisor = Column(String(50), nullable=True)

    wstart = Column(Date, nullable=True)
    wend = Column(Date, nullable=True)
    
    anomaly_flag = Column(Boolean, default=False)

    # Relationships
    team = relationship("Teams", back_populates="employee")
    pc = relationship("Pcs", back_populates="present_user", uselist=False)
    behavior_logs = relationship("Behavior_logs", back_populates="employee")
    blocking_history = relationship("BlockingHistory", back_populates="employee")