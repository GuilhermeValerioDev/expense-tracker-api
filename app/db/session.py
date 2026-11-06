from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Leave the session usable after a failed request instead of
        # returning a connection that is stuck in a failed transaction.
        db.rollback()
        raise
    finally:
        db.close()
