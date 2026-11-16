"""Kết nối CSDL. (Phân hệ của người phụ trách CSDL; để sẵn cho API chạy được.)"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

_settings = get_settings()
if _settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}  # endpoint đồng bộ chạy ở nhiều luồng
elif _settings.database_url.startswith("postgresql"):
    _connect_args = {"connect_timeout": 5}  # CSDL không trả lời thì báo lỗi sau 5 giây, không treo vô hạn
else:
    _connect_args = {}
engine = create_engine(_settings.database_url, pool_pre_ping=True, connect_args=_connect_args)
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
