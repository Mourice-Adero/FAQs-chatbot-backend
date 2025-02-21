from sqlalchemy import Column, Integer, String
from database import Base

class FAQs(Base):
    __tablename__ = "Frequently_Asked_Questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False, unique=True)
    answer = Column(String, nullable=False)
