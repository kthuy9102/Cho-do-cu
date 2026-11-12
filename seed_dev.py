from app.database import Base, SessionLocal, engine
from app import models  # noqa: nạp các model để create_all thấy bảng
from app.models import Category, Role, User
from app.security.passwords import hash_password

Base.metadata.create_all(engine)

with SessionLocal() as db:
    if db.query(User).first() is None:
        db.add_all([
            User(email="admin@example.com", hashed_password=hash_password("Admin12345"), full_name="Quan Tri", role=Role.admin),
            User(email="mod@example.com", hashed_password=hash_password("Mod12345678"), full_name="Kiem Duyet", role=Role.moderator),
            User(email="an@example.com", hashed_password=hash_password("Student123"), full_name="Nguyen Van An", role=Role.student),
            User(email="binh@example.com", hashed_password=hash_password("Student123"), full_name="Tran Thi Binh", role=Role.student),
            Category(name="Giáo trình", slug="giao-trinh"),
            Category(name="Đồ điện tử", slug="do-dien-tu"),
        ])
        db.commit()
print("seed xong")