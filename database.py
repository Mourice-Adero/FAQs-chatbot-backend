from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Database_url = "postgresql://postgres:8520@localhost:5432/FAQchatbot"

engine = create_engine(Database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
