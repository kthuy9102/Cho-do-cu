// Chạy dev (cổng 5500) thì gọi backend ở 8001; khi triển khai sau Nginx thì gọi cùng domain.
const API_ORIGIN = location.port === "5500" ? "http://localhost:8001" : "";
const API = API_ORIGIN + "/api/v1";

function getToken() { return localStorage.getItem("token"); }

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
      localStorage.removeItem("token");
      localStorage.removeItem("user");
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

addEventListener("unhandledrejection", e => {
  if (typeof toast === "function") toast(e.reason?.message || "Có lỗi xảy ra");
});

const EMO = { "do-dien-tu": "📱", "do-dung-hoc-tap": "✏️", "do-gia-dung": "🍳", "giao-trinh": "📚", "thoi-trang": "🧥" };
const CONDMAP = { like_new: 0, good: 1, fair: 2 };
const STMAP = { rejected: "hidden", hidden: "hidden" };
let CAT_IDS = [];
const img = u => u ? (u.startsWith("http") ? u : API_ORIGIN + u) : null;

async function loadFromApi() {
  const rc = await api("/categories");
  const cats = Array.isArray(rc) ? rc : rc.items;
  CAT_IDS = cats.map(c => c.id);
  CATS.length = 0;
  cats.forEach(c => CATS.push([c.name, EMO[c.slug] || "📦"]));

  const rl = await api("/listings?page_size=100");
  L = rl.items.map(x => ({
    id: x.id, t: x.title, p: x.price,
    c: CAT_IDS.indexOf(x.category.id),
    k: CONDMAP[x.condition] ?? 1,
    s: x.seller.id,
    a: Math.max(0, Math.floor((Date.now() - new Date(x.created_at)) / 864e5)),
    n: 1, im: x.thumbnail_url ? [img(x.thumbnail_url)] : null,
    st: STMAP[x.status] || x.status,
    rr: x.reject_reason || "",
    e: EMO[x.category.slug] || "📦", ds: ""
  }));
  rl.items.forEach(x => { U[x.seller.id] = { n: x.seller.full_name, h: "" }; });

  const fc = document.querySelector("#fc");
  if (fc) fc.innerHTML = '<option value="-1">Tất cả danh mục</option>' + CATS.map((c, i) => `<option value="${i}">${c[0]}</option>`).join("");
}