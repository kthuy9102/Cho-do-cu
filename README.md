#Chợ đồ cũ sinh viên
## Cài đặt
### Vào môi trường ảo(WSL2)
```bash
source .venv/bin/activate
```
### Chạy WebAPI
```bash
uvicorn app.main:app --reload
```
### Cài dặt trên Docker
```bash
docker compose up -d --build
```
### Thêm dữ liệu mẫu
```bash
docker compose exec api python seed.py
```
### Truy cập WebAPI
```bash
https://localhost:8080/docs
```
### Trang chủ 
```bash
https://localhost:8080
```
