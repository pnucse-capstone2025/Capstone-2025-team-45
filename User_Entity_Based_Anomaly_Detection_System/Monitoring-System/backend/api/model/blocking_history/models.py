from sqlalchemy import BigInteger, Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from model.database import Base

class BlockingHistory(Base):
	__tablename__ = 'blocking_history'
	blocking_history_id = Column(
        BigInteger,               
        primary_key=True,         
        autoincrement=True        
    )
	organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.organization_id'), nullable=False)
	pc_id = Column(String, ForeignKey('pcs.pc_id'), nullable=False)
	employee_id = Column(String, ForeignKey('employees.employee_id'), nullable=False)
	logon_time = Column(DateTime, nullable=True)
	blocking_time = Column(DateTime, nullable=True)
    
    #Relations
	organization = relationship("Organizations", back_populates="blocking_history")
	pc = relationship("Pcs", back_populates="blocking_history")
	employee = relationship("Employees", back_populates="blocking_history")