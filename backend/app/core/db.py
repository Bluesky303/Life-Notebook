from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    from app.models.asset import AssetAccountRecord, AssetInvestmentLogRecord, AssetTransactionRecord  # noqa: F401
    from app.models.feed import FeedRecord  # noqa: F401
    from app.models.knowledge import KnowledgeRecord  # noqa: F401
    from app.models.setting import SettingRecord  # noqa: F401
    from app.models.sleep import SleepLogRecord  # noqa: F401
    from app.models.task import TaskRecord  # noqa: F401

    Base.metadata.create_all(bind=engine)
