"""Nạp dữ liệu demo: 4 tài khoản (mỗi vai trò), danh mục và vài tin mẫu.

    python -m scripts.seed                  # chỉ nạp dữ liệu (bảng đã có do Alembic)
    python -m scripts.seed --create-tables  # tạo bảng bằng create_all rồi nạp (chỉ dùng khi dev)

Chạy lại nhiều lần an toàn: nếu đã có người dùng thì không làm gì.
Mật khẩu demo công khai trong README, KHÔNG dùng cho môi trường thật."""
import argparse
import sys

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import Category, ItemCondition, Listing, ListingStatus, Role, User
from app.security.passwords import hash_password

DEMO_ACCOUNTS = [
    ("admin@example.com", "Admin12345", "Quản Trị Viên", Role.admin),
    ("mod@example.com", "Mod12345678", "Kiểm Duyệt Viên", Role.moderator),
    ("an@example.com", "Student123", "Nguyễn Văn An", Role.student),
    ("binh@example.com", "Student123", "Trần Thị Bình", Role.student),
]
CATEGORIES = [("Giáo trình", "giao-trinh"), ("Đồ điện tử", "do-dien-tu"), ("Đồ dùng học tập", "do-dung-hoc-tap"), ("Quần áo", "quan-ao")]
SAMPLE_LISTINGS = [
    ("Giáo trình Giải tích 1", "Sách dùng một học kỳ, còn mới, không viết vẽ.", 45000, ItemCondition.like_new, "giao-trinh"),
    ("Máy tính Casio fx-580VN X", "Còn bảo hành, kèm hộp và hướng dẫn sử dụng.", 320000, ItemCondition.good, "do-dien-tu"),
    ("Tai nghe Bluetooth", "Pin dùng được khoảng 6 tiếng, có vài vết xước nhỏ.", 150000, ItemCondition.fair, "do-dien-tu"),
    ("Bộ bút vẽ kỹ thuật", "Đủ 12 cây, dùng cho môn Vẽ kỹ thuật.", 60000, ItemCondition.good, "do-dung-hoc-tap"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--create-tables", action="store_true", help="tạo bảng bằng create_all (chỉ dùng khi dev)")
    parser.add_argument("--force", action="store_true", help="cho phép chạy khi ENVIRONMENT=production")
    args = parser.parse_args()

    if get_settings().environment == "production" and not args.force:
        print("Từ chối: ENVIRONMENT=production. Mật khẩu demo không được dùng ở môi trường thật.")
        return 1
    if args.create_tables:
        Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if db.query(User).first() is not None:
            print("Đã có dữ liệu, bỏ qua seed.")
            return 0
        users = {}
        for email, password, name, role in DEMO_ACCOUNTS:
            user = User(email=email, hashed_password=hash_password(password), full_name=name, role=role)
            db.add(user)
            users[email] = user
        categories = {}
        for name, slug in CATEGORIES:
            category = Category(name=name, slug=slug)
            db.add(category)
            categories[slug] = category
        db.flush()
        for title, description, price, condition, slug in SAMPLE_LISTINGS:
            db.add(
                Listing(
                    seller_id=users["an@example.com"].id,
                    category_id=categories[slug].id,
                    title=title,
                    description=description,
                    price=price,
                    condition=condition,
                    status=ListingStatus.approved,
                )
            )
        db.commit()
    print("Seed xong. Tài khoản demo:")
    for email, password, _, role in DEMO_ACCOUNTS:
        print(f"  {role.value:<10} {email:<18} {password}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
