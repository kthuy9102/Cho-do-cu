# Front-end – Chợ đồ cũ sinh viên
    npm install
    npm run dev      # http://localhost:5173 (proxy /api -> http://localhost:8000)
## Hợp đồng API front-end đang gọi
POST /auth/register {full_name,email,password} · POST /auth/login {email,password} -> {access_token,user:{id,full_name,role}}
GET /categories · GET /listings?q&category_id&min_price&max_price&sort(newest|price_asc|price_desc)&page&size -> {items,total}
GET /listings/{id} · POST /listings (multipart: title,description,price,condition,category_id,images[]) · GET /listings/mine
GET /listings/pending · PATCH /listings/{id}/moderate {status: approved|rejected}
POST /listings/{id}/offers {price,message} · GET /offers/received · PATCH /offers/{id} {status: accepted|rejected}
POST /listings/{id}/reports {reason} · GET /reports · PATCH /reports/{id} {status}
Vai trò: user.role = "user" | "moderator". Ảnh: listing.images[].url
