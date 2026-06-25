from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, session


DATABASE_URL = "postgresql+psycopg://bism:supersecret@localhost:5432/expense_tracker"

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

        
