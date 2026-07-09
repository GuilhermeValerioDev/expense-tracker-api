from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, session
from dotenv import load_dotenv
import os
from config import get_env

DATABASE_URL = get_env("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        
