from .models import Dispute
from .session import SessionLocal, engine, Base

def init_db():
    from .models import Base
    Base.metadata.create_all(bind=engine) 