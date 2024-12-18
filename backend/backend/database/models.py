from sqlalchemy import Column, Integer, String, JSON, DateTime
from .session import Base
import datetime

class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(Integer, primary_key=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    party_one_name = Column(String)
    party_two_name = Column(String)
    context = Column(String, nullable=True)
    conversation = Column(String)
    
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    analysis_type = Column(String, default="dispute")
