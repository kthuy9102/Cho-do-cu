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
async function apiQuiet(path, opt = {}) {
  const h = { ...(opt.headers || {}) };
  const t = getToken();
  if (t) h.Authorization = "Bearer " + t;
  if (typeof opt.body === "string" && !h["Content-Type"]) h["Content-Type"] = "application/json";

  let res;
  try {
    res = await fetch(API + path, { ...opt, headers: h });
  } catch (e) {
    throw new Error("Không kết nối được máy chủ.");
  }

  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = data?.error?.message || "Lỗi HTTP " + res.status;
    const error = new Error(message);
    error.status = res.status;
    error.data = data;
    throw error;
  }
  return data;
}

addEventListener("unhandledrejection", e => {
  if (typeof toast === "function") toast(e.reason?.message || "Có lỗi xảy ra");
});

const EMO = { "do-dien-tu": "📱", "do-dung-hoc-tap": "✏️", "do-gia-dung": "🍳", "giao-trinh": "📚", "thoi-trang": "🧥" };
const CONDMAP = { new: 0, like_new: 0, good: 1, fair: 2, poor: 2 };
const STMAP = { rejected: "hidden", hidden: "hidden" };
let CAT_IDS = [];
const img = u => u ? (u.startsWith("http") ? u : API_ORIGIN + u) : null;

function mapListing(x) {
  return {
    id: x.id, t: x.title, p: x.price,
    c: Math.max(0, CAT_IDS.indexOf(x.category?.id)),
    k: CONDMAP[x.condition] ?? 1,
    s: x.seller?.id,
    a: Math.max(0, Math.floor((Date.now() - new Date(x.created_at || Date.now())) / 864e5)),
    n: x.images?.length || 1, im: x.images?.length ? x.images.map(i => img(i.url || i.image_url)).filter(Boolean) : (x.thumbnail_url ? [img(x.thumbnail_url)] : null),
    st: STMAP[x.status] || x.status || "pending",
    rr: x.reject_reason || "",
    e: EMO[x.category?.slug] || "📦", ds: x.description || ""
  };
}

function mapOffer(x) {
  return {
    id: x.id,
    l: x.listing?.id,
    f: x.buyer?.id,
    p: x.amount,
    m: x.message || "",
    st: x.status
  };
}


const ORDER_STMAP = { pending: "pending", confirmed: "confirmed", shipped: "shipping", completed: "done", cancelled: "cancelled" };
function mapOrder(x) {
  const created = new Date(x.created_at || Date.now()).getTime();
  const updated = new Date(x.updated_at || x.created_at || Date.now()).getTime();
  const ts = { pending: created };
  if (x.status === "confirmed") ts.confirmed = updated;
  if (x.status === "shipped") { ts.confirmed = created; ts.shipping = updated; }
  if (x.status === "completed") { ts.confirmed = created; ts.shipping = created; ts.done = updated; }
  if (x.status === "cancelled") ts.cancelled = updated;
  return {
    id: x.id, code: "DH" + String(x.id).padStart(6, "0"),
    offer_id: x.offer_id, l: x.listing?.id, b: x.buyer?.id, s: x.seller?.id,
    p: x.amount, name: x.delivery_name || x.buyer?.full_name || "",
    phone: x.delivery_phone || "", addr: x.delivery_address || "",
    pay: x.payment_method || "Thỏa thuận trực tiếp", note: x.note || "",
    st: ORDER_STMAP[x.status] || x.status, ts, eta: updated + 2 * 864e5, rv: false
  };
}
function mapNotification(x) {
  const link = x.resource_type === "order" ? "orders:buy" :
    x.event_type === "offer_received" ? "mine" : "orders:buy";
  let userId = null;
  try { userId = JSON.parse(sessionStorage.getItem("cdcsv_buser") || "null")?.id ?? null; } catch (_) {}
  return { id: x.id, to: userId, t: x.title + (x.body ? " · " + x.body : ""),
    link, ic: "🔔", ts: new Date(x.created_at || Date.now()).getTime(), read: !!x.read_at };
}

async function loadFromApi() {
  const rc = await api("/categories");
  const cats = Array.isArray(rc) ? rc : rc.items;
  CAT_IDS = cats.map(c => c.id);
  CATS.length = 0;
  cats.forEach(c => CATS.push([c.name, EMO[c.slug] || "📦"]));

  const rl = await api("/listings?page_size=100");
  L = rl.items.map(mapListing);
  RP = [];
  rl.items.forEach(x => { if (x.seller) U[x.seller.id] = { n: x.seller.full_name, h: "" }; });

  if (getToken()) {
    const mine = await apiQuiet("/listings/mine?page_size=100").catch(e => {
      console.warn("Không lấy được tin của tôi:", e.message); return { items: [] };
    });
    (mine.items || []).forEach(x => {
      const i = L.findIndex(l => l.id === x.id);
      if (i >= 0) L[i] = mapListing(x); else L.push(mapListing(x));
      if (x.seller) U[x.seller.id] = U[x.seller.id] || { n: x.seller.full_name, h: "" };
    });

    const [sent, received, favorites, orders, notifications] = await Promise.all([
      apiQuiet("/offers/sent?page_size=100").catch(e => { console.warn("Offers sent:", e.message); return { items: [] }; }),
      apiQuiet("/offers/received?page_size=100").catch(e => { console.warn("Offers received:", e.message); return { items: [] }; }),
      apiQuiet("/favorites?page_size=100").catch(e => { console.warn("Favorites:", e.message); return { items: [] }; }),
      apiQuiet("/orders?page_size=100"),
      apiQuiet("/notifications?page_size=100")
    ]);
    const offers = [...(sent.items || []), ...(received.items || [])];
    O = [...new Map(offers.map(x => [x.id, x])).values()].map(mapOffer);
    ORD = (orders.items || []).map(mapOrder);
    NOTI = (notifications.items || []).map(mapNotification);
    S.fav = new Set((favorites.items || []).map(x => x.id));

    const sellerIds = [...new Set(L.map(x => x.s).filter(Boolean))];
    const reviewPages = await Promise.all(sellerIds.map(id =>
      apiQuiet("/users/" + id + "/reviews?page_size=100").catch(e => {
        console.warn("Reviews for seller " + id + ":", e.message); return { items: [] };
      })
    ));
    R = reviewPages.flatMap(page => (page.items || []).map(x => ({
      l: (O.find(o => o.id === x.offer_id) || {}).l || null,
      offer_id: x.offer_id, to: x.seller_id, f: x.reviewer?.id,
      star: x.rating, x: x.comment || ""
    })));
  } else {
    O = [];
    S.fav = new Set();
  }

  const fc = document.querySelector("#fc");
  if (fc) fc.innerHTML = '<option value="-1">Tất cả danh mục</option>' + CATS.map((c, i) => `<option value="${i}">${c[0]}</option>`).join("");
}
