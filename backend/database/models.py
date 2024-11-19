from sqlalchemy import Column, Integer, String, JSON, DateTime
from .session import Base
import datetime
from .types import ArgumentResultType
class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(Integer, primary_key=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    party_one_name = Column(String)
    party_two_name = Column(String)
    context1 = Column(String)
    context2 = Column(String)
    conversation = Column(String)
    
    #result = Column(JSON, nullable=True)
    result = Column(ArgumentResultType, nullable=True)
    error = Column(String, nullable=True)
