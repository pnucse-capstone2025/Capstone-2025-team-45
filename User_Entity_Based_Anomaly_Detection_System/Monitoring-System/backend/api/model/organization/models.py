import uuid
from datetime import datetime

from sqlalchemy import Column, BigInteger,  String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID  
from model.database import Base

class Organizations(Base):
    __tablename__ = 'organizations'
    organization_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )
    organization_name = Column(String(50), unique=True, index=True, nullable=False)
    authentication_code = Column(String(128), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    security_managers = relationship("Security_managers", back_populates="organization")
    functional_units = relationship("FunctionalUnits", back_populates="organization")
    pcs = relationship("Pcs", back_populates="organization")
    routers = relationship("Routers", back_populates="organization")
    anomaly_detection_histories = relationship("AnomalyDetectionHistories", back_populates="organization")
    blocking_history = relationship("BlockingHistory", back_populates="organization")