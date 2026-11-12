"""Kết nối CSDL. (Phân hệ của người phụ trách CSDL; để sẵn cho API chạy được.)"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """Mỗi request một session; luôn đóng khi xong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
