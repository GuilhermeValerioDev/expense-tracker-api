from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

class User(Base):
    __tablename__ = "users"