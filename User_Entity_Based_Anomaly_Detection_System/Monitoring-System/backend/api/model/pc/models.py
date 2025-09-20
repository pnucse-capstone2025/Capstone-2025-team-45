import enum
from datetime import datetime

from sqlalchemy import Column, BigInteger,  String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID  
from model.database import Base

class LogonState(enum.Enum):
    ON = "logged_in"
    OFF = "logged_out"
    UNKNOWN = "unknown"

class Pcs(Base):
    __tablename__ = 'pcs'
    pc_id = Column( 
        String(80),
        primary_key=True,
        unique=True,
        nullable=False,
        index=True
    )
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id"), nullable=False)
    ip_address = Column(String(15), unique=False, nullable=True)
    mac_address = Column(String(17), unique=False, nullable=True)
    access_flag = Column(Boolean, default=True, nullable=False)
    present_user_id = Column(String(20), ForeignKey("employees.employee_id"), nullable=True, default=None)
    current_state = Column(Enum(LogonState), default=LogonState.OFF, nullable=False)

    # Relationships
    present_user = relationship("Employees", back_populates="pc", uselist=False)
    organization = relationship("Organizations", back_populates="pcs", uselist=False)
    behavior_logs = relationship("Behavior_logs", back_populates="pc")
    blocking_history = relationship("BlockingHistory", back_populates="pc")