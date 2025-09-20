import enum
from datetime import datetime

from sqlalchemy import Column, Integer,  String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB 
from model.database import Base


class Routers(Base):
    __tablename__ = 'routers'

    router_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id"), nullable=False)
    control_ip = Column(String(15), nullable=False)
    state = Column(String(10), default="UNKNOWN",  nullable=False)

    connected_mac_addresses = Column(JSONB, nullable=True)
    # Relationships
    organization = relationship("Organizations", back_populates="routers", uselist=False)