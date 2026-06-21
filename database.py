from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+psycopg://bism:supersecret@localhost:5432/expense_tracker"

engine = create_engine(DATABASE_URL)

class Base(DeclarativeBase):
    pass

