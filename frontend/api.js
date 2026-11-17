// Cùng cấu hình API cho Frontend chạy độc lập (Live Server :5500) và Docker/Nginx.
const API_ORIGIN = location.port === "5500"
  ? `${location.protocol}//${location.hostname}:8001`
  : "";
const API = API_ORIGIN + "/api/v1";

function getToken() {
  return localStorage.getItem("cdcsv_token");
}

async function api(path, opt = {}) {
  const h = { ...(opt.headers || {}) };
  if (typeof opt.body === "string" && !h["Content-Type"]) h["Content-Type"] = "application/json";
  const token = getToken();
  if (token) h.Authorization = "Bearer " + token;

  let res;
  try {
    res = await fetch(API + path, { ...opt, headers: h });
  } catch (error) {
    throw new Error("Không kết nối được Backend. Kiểm tra API tại cổng 8001 hoặc cấu hình Docker.");
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("/auth/")) {
      ["cdcsv_token", "cdcsv_buser", "cdcsv_session", "cdcsv_admin"].forEach(key => localStorage.removeItem(key));
      if (!location.pathname.endsWith("login.html")) location.href = "login.html#login";
      throw new Error("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại (401).");
    }
    if (res.status === 403) throw new Error(data?.error?.message || "Bạn không có quyền thực hiện thao tác này (403).");
    if (res.status === 429) throw new Error(data?.error?.message || "Bạn thao tác quá nhanh hoặc vượt giới hạn cho phép (429).");
    let message = data?.error?.message || data?.detail || "Lỗi " + res.status;
    const details = data?.error?.details;
    if (Array.isArray(details) && details.length) {
      message += ": " + details.map(item => item.msg || item.message || JSON.stringify(item)).join("; ");
    }
    throw new Error(message);
  }
  return data;
}

addEventListener("unhandledrejection", event => {
  if (typeof toast === "function") toast(event.reason?.message || "Có lỗi xảy ra");
});

const EMO = {
  "do-dien-tu": "📱", "do-dung-hoc-tap": "✏️", "do-gia-dung": "🍳",
  "giao-trinh": "📚", "thoi-trang": "🧥", "quan-ao": "🧥"
};
const CONDMAP = { like_new: 0, good: 1, fair: 2 };
const STMAP = { rejected: "hidden", hidden: "hidden" };
let CAT_IDS = [];
const img = url => url ? (url.startsWith("http") ? url : API_ORIGIN + url) : null;

async function loadFromApi() {
  const [categories, result] = await Promise.all([
    api("/categories"),
    api("/listings?page=1&page_size=100&sort=newest")
  ]);

  if (!Array.isArray(categories)) throw new Error("API danh mục trả về dữ liệu không hợp lệ.");
  if (!result || !Array.isArray(result.items)) throw new Error("API tin đăng trả về dữ liệu không hợp lệ.");

  CAT_IDS = categories.map(category => category.id);
  CATS.length = 0;
  categories.forEach(category => CATS.push([category.name, EMO[category.slug] || "📦"]));

  L = result.items.map(item => ({
    id: item.id,
    t: item.title,
    p: item.price,
    c: CAT_IDS.indexOf(item.category.id),
    k: CONDMAP[item.condition] ?? 1,
    s: item.seller.id,
    a: Math.max(0, Math.floor((Date.now() - new Date(item.created_at)) / 864e5)),
    n: item.thumbnail_url ? 1 : 0,
    im: item.thumbnail_url ? [img(item.thumbnail_url)] : null,
    st: STMAP[item.status] || item.status,
    rr: item.reject_reason || "",
    e: EMO[item.category.slug] || "📦",
    ds: item.description || ""
  }));

  result.items.forEach(item => {
    U[item.seller.id] = { n: item.seller.full_name, h: "" };
  });

  const categoryFilter = document.querySelector("#fc");
  if (categoryFilter) {
    categoryFilter.innerHTML = '<option value="-1">Tất cả danh mục</option>' +
      CATS.map((category, index) => `<option value="${index}">${category[0]}</option>`).join("");
  }
}
