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
  const signedIn = typeof session === "function" && !!session();
  const requests = [
    api("/categories"),
    api("/listings?page=1&page_size=100&sort=newest"),
    signedIn ? api("/listings/mine?page=1&page_size=100").catch(() => ({ items: [] })) : Promise.resolve({ items: [] }),
    signedIn ? api("/favorites?page=1&page_size=100").catch(() => ({ items: [] })) : Promise.resolve({ items: [] }),
    signedIn ? api("/offers/sent?page=1&page_size=100").catch(() => ({ items: [] })) : Promise.resolve({ items: [] }),
    signedIn ? api("/offers/received?page=1&page_size=100").catch(() => ({ items: [] })) : Promise.resolve({ items: [] })
  ];
  const [categories, publicResult, mineResult, favoriteResult, sentResult, receivedResult] = await Promise.all(requests);

  if (!Array.isArray(categories)) throw new Error("API danh mục trả về dữ liệu không hợp lệ.");
  if (!publicResult || !Array.isArray(publicResult.items)) throw new Error("API tin đăng trả về dữ liệu không hợp lệ.");

  CAT_IDS = categories.map(category => category.id);
  CATS.length = 0;
  categories.forEach(category => CATS.push([category.name, EMO[category.slug] || "📦"]));

  // Không dùng dữ liệu giao dịch giả từ bản demo cũ.
  RP = [];
  ORD = [];
  NOTI = [];
  S.fav = new Set((favoriteResult.items || []).map(item => item.id));

  const byId = new Map();
  [...publicResult.items, ...(mineResult.items || [])].forEach(item => byId.set(item.id, item));
  const allItems = [...byId.values()];

  L = allItems.map(item => ({
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
    ds: ""
  }));

  allItems.forEach(item => {
    U[item.seller.id] = { ...(U[item.seller.id] || {}), n: item.seller.full_name, h: "" };
  });

  const offers = [...(sentResult.items || []), ...(receivedResult.items || [])];
  const offerById = new Map();
  offers.forEach(item => offerById.set(item.id, item));
  O = [...offerById.values()].map(item => ({
    id: item.id,
    l: item.listing.id,
    f: item.buyer.id,
    p: item.amount,
    m: item.message || "",
    st: item.status
  }));
  offers.forEach(item => {
    U[item.buyer.id] = { ...(U[item.buyer.id] || {}), n: item.buyer.full_name, h: "" };
  });

  // Bổ sung các tin đã bán trong đề nghị đã chấp nhận để người mua vẫn xem được lịch sử giao dịch.
  offers.forEach(item => {
    const listing = item.listing;
    if (!L.some(existing => existing.id === listing.id)) {
      L.push({
        id: listing.id, t: listing.title, p: listing.price, c: -1, k: 1,
        s: listing.seller_id, a: 0, n: 1, im: null,
        st: STMAP[listing.status] || listing.status, rr: "", e: "📦", ds: ""
      });
    }
  });

  const sellerIds = [...new Set([
    ...allItems.map(item => item.seller.id),
    ...offers.map(item => item.listing.seller_id)
  ])];
  const [profiles, reviewPages] = await Promise.all([
    Promise.all(sellerIds.map(id => api(`/users/${id}`).catch(() => null))),
    Promise.all(sellerIds.map(id => api(`/users/${id}/reviews?page=1&page_size=100`).catch(() => ({ items: [] }))))
  ]);
  profiles.filter(Boolean).forEach(profile => {
    U[profile.id] = {
      ...(U[profile.id] || {}),
      n: profile.full_name,
      h: "",
      rating_avg: profile.rating_avg,
      review_count: profile.review_count
    };
  });
  const reviews = reviewPages.flatMap(page => page.items || []);
  R = reviews.map(review => {
    const offer = offerById.get(review.offer_id);
    return {
      l: offer?.listing.id,
      to: review.seller_id,
      f: review.reviewer.id,
      star: review.rating,
      x: review.comment || ""
    };
  }).filter(review => review.l != null);

  const categoryFilter = document.querySelector("#fc");
  if (categoryFilter) {
    categoryFilter.innerHTML = '<option value="-1">Tất cả danh mục</option>' +
      CATS.map((category, index) => `<option value="${index}">${category[0]}</option>`).join("");
  }
}
