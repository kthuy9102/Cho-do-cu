// Chạy dev (cổng 5000 hoặc 5500) thì gọi backend ở 8001; khi triển khai sau Nginx thì gọi cùng domain.
const API_ORIGIN = ["5000", "5500"].includes(location.port) ? "http://localhost:8001" : "";
const API = API_ORIGIN + "/api/v1";

// Token lưu theo từng tab (sessionStorage) nên mỗi tab giữ tài khoản riêng
function getToken() { return sessionStorage.getItem("cdcsv_token"); }

async function api(path, opt = {}) {
  const h = { ...(opt.headers || {}) };
  if (typeof opt.body === "string" && !h["Content-Type"]) h["Content-Type"] = "application/json";
  const t = getToken();
  if (t) h.Authorization = "Bearer " + t;

  let res;
  try {
    res = await fetch(API + path, { ...opt, headers: h });
  } catch (e) {
    throw new Error("Không kết nối được máy chủ. Hãy kiểm tra backend đã chạy chưa.");
  }
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/auth/")) {
      sessionStorage.removeItem("cdcsv_token");
      sessionStorage.removeItem("cdcsv_buser");
      if (!location.pathname.endsWith("login.html")) location.href = "login.html#login";
      throw new Error("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại (401).");
    }
    if (res.status === 403) throw new Error("Bạn không có đủ quyền thực hiện thao tác này (403).");
    if (res.status === 429) throw new Error("Bạn thao tác quá nhanh hoặc vượt giới hạn cho phép (429).");
    let msg = data?.error?.message || "Lỗi " + res.status;
    const d = data?.error?.details;
    if (Array.isArray(d) && d.length) msg += ": " + d.map(x => x.msg || x.message || JSON.stringify(x)).join("; ");
    throw new Error(msg);
  }
  return data;
}

// Gọi "im lặng": lỗi không xóa token, không đá về trang đăng nhập
async function apiQuiet(path) {
  const t = getToken();
  const res = await fetch(API + path, { headers: t ? { Authorization: "Bearer " + t } : {} });
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.json();
}

addEventListener("unhandledrejection", e => {
  if (typeof toast === "function") toast(e.reason?.message || "Có lỗi xảy ra");
});

const EMO = { "do-dien-tu": "📱", "do-dung-hoc-tap": "✏️", "do-gia-dung": "🍳", "giao-trinh": "📚", "thoi-trang": "🧥" };
const CONDMAP = { like_new: 0, good: 1, fair: 2 };
const STMAP = { rejected: "hidden", hidden: "hidden" };
let CAT_IDS = [];
const img = u => u ? (u.startsWith("http") ? u : API_ORIGIN + u) : null;

function mapListing(x) {
  return {
    id: x.id, t: x.title, p: x.price,
    c: CAT_IDS.indexOf(x.category?.id),
    k: CONDMAP[x.condition] ?? 1,
    s: x.seller?.id,
    a: Math.max(0, Math.floor((Date.now() - new Date(x.created_at || Date.now())) / 864e5)),
    n: 1, im: x.thumbnail_url ? [img(x.thumbnail_url)] : null,
    st: STMAP[x.status] || x.status || "pending",
    rr: x.reject_reason || "",
    e: EMO[x.category?.slug] || "📦", ds: x.description || ""
  };
}

async function loadFromApi() {
  // 1. Danh mục
  const rc = await api("/categories");
  const cats = Array.isArray(rc) ? rc : rc.items;
  CAT_IDS = cats.map(c => c.id);
  CATS.length = 0;
  cats.forEach(c => CATS.push([c.name, EMO[c.slug] || "📦"]));

  // 2. Tin công khai (đã duyệt)
  const rl = await api("/listings?page_size=100");
  L = rl.items.map(mapListing);
  rl.items.forEach(x => { U[x.seller.id] = { n: x.seller.full_name, h: "" }; });

  // 3. Tin của chính mình, mọi trạng thái (chờ duyệt, bị ẩn...)
  if (getToken()) {
    try {
      const rm = await apiQuiet("/listings/mine?page_size=100");
      rm.items.forEach(x => {
        const i = L.findIndex(l => l.id === x.id);
        if (i >= 0) L[i] = mapListing(x);
        else L.push(mapListing(x));
        U[x.seller.id] = U[x.seller.id] || { n: x.seller.full_name, h: "" };
      });
    } catch (e) { console.warn("Không lấy được tin của tôi:", e.message); }
  }

  // 4. Ô chọn danh mục
  const fc = document.querySelector("#fc");
  if (fc) fc.innerHTML = '<option value="-1">Tất cả danh mục</option>' + CATS.map((c, i) => `<option value="${i}">${c[0]}</option>`).join("");
}