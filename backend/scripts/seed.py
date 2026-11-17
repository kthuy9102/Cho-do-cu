"""Nạp dữ liệu demo: 4 tài khoản (mỗi vai trò), danh mục và 14 tin mẫu.

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

CATEGORIES = [
    ("Giáo trình", "giao-trinh"),
    ("Đồ điện tử", "do-dien-tu"),
    ("Đồ dùng học tập", "do-dung-hoc-tap"),
    ("Thời trang", "thoi-trang"),
    ("Đồ gia dụng", "do-gia-dung"),
]

SAMPLE_LISTINGS = [
    ("iPhone 11 64GB trắng", "Bản quốc tế 64GB, ngoại hình đẹp, pin ổn định.", 6200000, ItemCondition.good, "do-dien-tu"),
    ("Giày MLB size 42", "Giày ít đi, đế còn mới 99%, đầy đủ hộp.", 850000, ItemCondition.like_new, "thoi-trang"),
    ("Tai nghe không dây", "Kết nối Bluetooth nhạy, pin dùng liên tục 4-5 tiếng.", 420000, ItemCondition.good, "do-dien-tu"),
    ("Giáo trình Giải tích 1", "Sách giáo trình đại cương, có ghi chú bài tập.", 45000, ItemCondition.fair, "giao-trinh"),
    ("Macbook Air M1 2020", "RAM 8GB SSD 256GB, hoạt động mượt mà, kèm sạc zin.", 13500000, ItemCondition.good, "do-dien-tu"),
    ("Bàn phím cơ Keychron K2", "Switch gõ êm, fullbox đầy đủ phụ kiện và cáp sạc.", 1200000, ItemCondition.like_new, "do-dien-tu"),
    ("Áo khoác bomber đen", "Chất vải dày dặn, giữ ấm tốt, không xù lông.", 180000, ItemCondition.good, "thoi-trang"),
    ("Nồi cơm điện mini 1L", "Nồi nhỏ gọn phù hợp cho 1-2 sinh viên ở trọ.", 150000, ItemCondition.good, "do-gia-dung"),
    ("Bàn học gấp gọn", "Mặt gỗ chắc chắn, chân gấp gọn tiết kiệm diện tích.", 220000, ItemCondition.good, "do-gia-dung"),
    ("Máy tính Casio fx-580VN X", "Máy chính hãng còn tem, phím bấm nảy, màn hình rõ.", 350000, ItemCondition.like_new, "do-dung-hoc-tap"),
    ("Sách Lập trình Python cơ bản", "Sách hướng dẫn nhập môn Python cho sinh viên CNTT.", 60000, ItemCondition.good, "giao-trinh"),
    ("Laptop Dell Inspiron 15", "Core i5, RAM 8GB, SSD 256GB, phù hợp học tập và văn phòng.", 7800000, ItemCondition.good, "do-dien-tu"),
    ("Đèn học LED chống cận", "Đèn kẹp bàn 3 mức sáng, cổng sạc USB tiện lợi.", 90000, ItemCondition.like_new, "do-dung-hoc-tap"),
    ("Balo laptop chống sốc", "Đựng vừa laptop 15.6 inch, nhiều ngăn chứa đồ.", 190000, ItemCondition.good, "do-dung-hoc-tap"),
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