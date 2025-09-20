from datetime import datetime
from sqlalchemy import Column, BigInteger,  String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID  
from model.database import Base

class AnomalyDetectionHistories(Base):
    __tablename__ = 'anomaly_detection_histories'
    anomaly_detection_history_id = Column(
        BigInteger,               
        primary_key=True,         
        autoincrement=True        
    )
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.organization_id'), nullable=False)
    run_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    results = Column(String, nullable=True)  

    # Relationships
    organization = relationship("Organizations", back_populates="anomaly_detection_histories")
