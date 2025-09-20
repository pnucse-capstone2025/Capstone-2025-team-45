from datetime import datetime

from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime, ForeignKey, TEXT
from sqlalchemy.orm import relationship  
from model.database import Base

class Behavior_logs(Base):
    __tablename__ = 'behavior_logs'
    event_id = Column( 
        String(64),
        primary_key=True
    )
    employee_id = Column(String(20), ForeignKey("employees.employee_id"), nullable=False)
    pc_id = Column(String(80), ForeignKey("pcs.pc_id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String(10), nullable=False)

    # Relationships
    employee = relationship("Employees", back_populates="behavior_logs")
    pc = relationship("Pcs", back_populates="behavior_logs")
    http_log = relationship("Http_logs", back_populates="behavior_log", uselist=False)
    email_log = relationship("Email_logs", back_populates="behavior_log", uselist=False)
    device_log = relationship("Device_logs", back_populates="behavior_log", uselist=False)
    logon_log = relationship("Logon_logs", back_populates="behavior_log", uselist=False)
    file_log = relationship("File_logs", back_populates="behavior_log", uselist=False)

class Http_logs(Base):
    __tablename__ = "http_logs"

    event_id = Column(String(64), ForeignKey("behavior_logs.event_id"), primary_key=True)
    url = Column(String(2048), nullable=False)

    behavior_log = relationship("Behavior_logs", back_populates="http_log")

class Email_logs(Base):
    __tablename__ = "email_logs"

    event_id = Column(String(64), ForeignKey("behavior_logs.event_id"), primary_key=True)
    to = Column(String(500), nullable=False)
    cc = Column(String(500))
    bcc = Column(String(500))
    from_addr = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    attachment = Column(Integer, nullable=False)

    behavior_log = relationship("Behavior_logs", back_populates="email_log")

class Device_logs(Base):
    __tablename__ = "device_logs"

    event_id = Column(String(64), ForeignKey("behavior_logs.event_id"), primary_key=True)
    activity = Column(String(13), nullable=False)

    behavior_log = relationship("Behavior_logs", back_populates="device_log")

class Logon_logs(Base):
    __tablename__ = "logon_logs"

    event_id = Column(String(64), ForeignKey("behavior_logs.event_id"), primary_key=True)
    activity = Column(String(7), nullable=False)

    behavior_log = relationship("Behavior_logs", back_populates="logon_log")

class File_logs(Base):
    __tablename__ = "file_logs"

    event_id = Column(String(64), ForeignKey("behavior_logs.event_id"), primary_key=True)
    filename = Column(String(255), nullable=False)

    behavior_log = relationship("Behavior_logs", back_populates="file_log")
