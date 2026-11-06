from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


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


def init_db() -> None:
    """Create tables that do not exist yet.

    Temporary bootstrap until Alembic migrations land. Importing ``models``
    here makes sure every table is registered on ``Base.metadata``.
    """
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
