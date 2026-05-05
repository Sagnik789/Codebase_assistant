from sqlalchemy import Column, Integer, String, Text
from app.services.database import Base

class QueryHistory(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    answer = Column(Text)