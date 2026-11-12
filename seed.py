from app.database import Base, engine, SessionLocal
from app.models import Category, Listing, User, ListingImage, Role, ItemCondition, ListingStatus  # Đảm bảo import đúng đường dẫn models của mày
from app.security.passwords import hash_password

def seed_data():
    print("⏳ Đang khởi tạo các bảng (nếu chưa có)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Kiểm tra xem DB đã có dữ liệu chưa để tránh chạy trùng
        if db.query(Category).count() > 0:
            print("✅ Database đã có dữ liệu, bỏ qua bước seed.")
            return

        print("🌱 Bắt đầu nạp dữ liệu mẫu...")

        # 1. Tạo User mẫu (người bán)
        seller = User(
            email="zael0911@gmail.com",
            hashed_password=hash_password("123456"),
            full_name="PHAM GIA HUY",
            student_id="2412111028",
            role=Role.student,  # <-- SỬA THÀNH Role.student
            is_active=True
        )
        db.add(seller)
        db.commit()
        db.refresh(seller)

        # 2. Tạo Danh mục mẫu
        cat_sach = Category(name="Giáo trình", slug="giao-trinh")
        cat_may_tinh = Category(name="Máy tính", slug="may-tinh")
        cat_quat = Category(name="Quạt", slug="quat")
        
        db.add_all([cat_sach, cat_may_tinh, cat_quat])
        db.commit()
        db.refresh(cat_sach)
        db.refresh(cat_may_tinh)
        db.refresh(cat_quat)

        # 3. Tạo Sản phẩm mẫu
        items = [
            Listing(
                title="Giáo trình Giải tích 1 - ĐH Bách Khoa",
                description="Sách còn mới 90%, không ghi chú.",
                price=50000,
                condition=ItemCondition.like_new,
                category_id=cat_sach.id,
                seller_id=seller.id,
                status="approved"
            ),
            Listing(
                title="Chuột không dây Logitech M330",
                description="Chuột im lặng, pin trâu.",
                price=150000,
                condition=ItemCondition.good,
                category_id=cat_may_tinh.id,
                seller_id=seller.id,
                status="approved"
            ),
            Listing(
                title="Quạt tích điện Tiross",
                description="Quạt sạc 3 nấc, chạy 5 tiếng.",
                price=200000,
                condition=ItemCondition.fair,
                category_id=cat_quat.id,
                seller_id=seller.id,
                status="approved"
            )
        ]
        
        db.add_all(items)
        db.commit()
        print("🎉 Đã nạp dữ liệu mẫu thành công!")

    except Exception as e:
        print(f"❌ Lỗi khi seed dữ liệu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()