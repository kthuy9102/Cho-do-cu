/* Trang kiểm duyệt dùng dữ liệu thật từ FastAPI. */
let tab = "pending";

const REPORT_LABELS = {
  spam: "Spam",
  fraud: "Lừa đảo",
  prohibited_item: "Hàng cấm",
  inappropriate: "Nội dung không phù hợp",
  other: "Lý do khác"
};

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.style.display = "block";
  clearTimeout(toast.handle);
  toast.handle = setTimeout(() => node.style.display = "none", 3000);
}
function ADM() {
  try {
    const user = JSON.parse(localStorage.getItem(AUTH_BUSER_KEY) || "null");
    return !!localStorage.getItem(AUTH_TOKEN_KEY) && !!user &&
      ["admin", "moderator"].includes(String(user.role || "").toLowerCase());
  } catch {
    return false;
  }
}
function stB(listing) {
  return ({
    pending: '<span class="badge w">Chờ duyệt</span>',
    approved: '<span class="badge">Đang bán</span>',
    sold: '<span class="badge">Đã bán</span>',
    rejected: '<span class="badge x">Bị từ chối</span>',
    hidden: '<span class="badge x">Đã ẩn</span>'
  })[listing.st] || "";
}
function mapListing(item) {
  return {
    id: item.id,
    t: item.title,
    p: item.price,
    c: CATS.findIndex(category => category[0] === item.category.name),
    k: ({ like_new: 0, good: 1, fair: 2, new: 0, poor: 2 })[item.condition] ?? 1,
    s: item.seller.id,
    a: Math.max(0, Math.floor((Date.now() - new Date(item.created_at)) / 864e5)),
    n: item.images?.length || 0,
    im: item.images?.map(image => img(image.url)) || null,
    st: item.status,
    e: "📦",
    ds: item.description || "",
    rr: item.reject_reason || ""
  };
}
async function loadModerationData() {
  const [categories, pending, approved, sold, rejected, hidden, reports] = await Promise.all([
    api("/categories"),
    ...["pending", "approved", "sold", "rejected", "hidden"].map(status =>
      api("/moderation/listings?status=" + status + "&page=1&page_size=100")
    ),
    api("/moderation/reports?status=open&page=1&page_size=100")
  ]);

  CATS.length = 0;
  categories.forEach(category => CATS.push([category.name, "📦"]));
  const items = [...pending.items, ...approved.items, ...sold.items, ...rejected.items, ...hidden.items];
  const unique = new Map(items.map(item => [item.id, item]));
  L = [...unique.values()].map(mapListing);

  U = U || {};
  L.forEach(item => {
    const source = items.find(row => row.id === item.id);
    U[item.s] = { n: source.seller.full_name, h: "" };
  });
  RP = reports.items.map(report => ({
    id: report.id,
    l: report.listing.id,
    f: report.reporter.id,
    x: (REPORT_LABELS[report.reason_code] || report.reason_code) +
      (report.detail ? ": " + report.detail : ""),
    open: report.status === "open"
  }));
}
function loginHtml() {
  return `<div class="card pad" style="max-width:420px;margin:40px auto">
    <div class="sh"><span>🛡️</span>Đăng nhập quản trị</div>
    <div class="db" style="padding:0">
      <label class="f">Email<input id="ae" type="email" autocomplete="username"></label>
      <label class="f">Mật khẩu<input id="ap" type="password" autocomplete="current-password" onkeydown="if(event.key==='Enter')adminIn()"></label>
      <span class="err" id="aer"></span>
      <button class="btn" onclick="adminIn()">Đăng nhập</button>
      <a href="index.html" class="mut">← Về trang chợ sinh viên</a>
    </div>
  </div>`;
}
async function adminIn() {
  const email = $("#ae").value.trim().toLowerCase();
  const password = $("#ap").value;
  const button = $("#app").querySelector("button.btn");
  const error = $("#aer");
  error.textContent = "";
  if (button) button.disabled = true;
  try {
    const result = await login(email, password);
    if (!result.ok) {
      error.textContent = result.msg || "Đăng nhập thất bại.";
      return;
    }
    if (!["admin", "moderator"].includes(String(result.role || "").toLowerCase())) {
      logout();
      error.textContent = "Tài khoản này không có quyền kiểm duyệt.";
      return;
    }
    await render();
  } catch (exception) {
    console.error(exception);
    error.textContent = "Không thể đăng nhập. Vui lòng thử lại.";
  } finally {
    if (button) button.disabled = false;
  }
}
function rowA(listing, actions, sub = "") {
  const image = listing.im?.[0]
    ? `<div class="tile"><img src="${listing.im[0]}" alt=""></div>`
    : `<div class="tile"><span>${listing.e}</span></div>`;
  return `<div class="ls">${image}<div class="gr" onclick="view(${listing.id})">
    <b>${esc(listing.t)}</b><span class="mut">${vnd(listing.p)} · ${esc(U[listing.s]?.n || "Người bán")} · ${ago(listing.a)}${sub}</span>
  </div><div class="acts">${actions}</div></div>`;
}
function dash() {
  const pending = L.filter(item => item.st === "pending");
  const reports = RP.filter(report => report.open);
  const all = L.filter(item => item.st !== "pending");
  const stats = [
    [pending.length, "Chờ duyệt"],
    [L.filter(item => item.st === "approved").length, "Đang bán"],
    [L.filter(item => item.st === "sold").length, "Đã bán"],
    [L.filter(item => item.st === "hidden" || item.st === "rejected").length, "Đã ẩn / từ chối"],
    [reports.length, "Báo cáo mở"]
  ].map(([count, label]) => `<div class="card pad" style="text-align:center"><div class="pr" style="font-size:24px">${count}</div><div class="mut">${label}</div></div>`).join("");

  const tabs = [
    ["pending", `Tin chờ duyệt (${pending.length})`],
    ["reports", `Báo cáo vi phạm (${reports.length})`],
    ["all", `Tất cả tin (${L.length})`]
  ];
  let content = `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-bottom:12px">${stats}</div>
    <div class="card tabs">${tabs.map(([key, label]) => `<button class="tab ${tab === key ? "on" : ""}" onclick="tab='${key}';render() ">${label}</button>`).join("")}</div><div class="card">`;

  if (tab === "pending") {
    content += pending.length
      ? pending.map(item => rowA(item,
          `<button class="btn sm" onclick="setSt(${item.id},'approved')">Duyệt</button>
           <button class="btn sm r" onclick="askReason(${item.id})">Từ chối</button>`)).join("")
      : '<div class="empty">Không còn tin nào chờ duyệt.</div>';
  } else if (tab === "reports") {
    content += reports.length
      ? reports.map(report => {
          const listing = L.find(item => item.id === report.l);
          if (!listing) return "";
          return rowA(listing,
            `<button class="btn sm r" onclick="resolve(${report.id},true)">Ẩn tin</button>
             <button class="btn sm o" onclick="resolve(${report.id},false)">Bỏ qua</button>`,
            ` · Báo cáo: ${esc(report.x)} · ${esc(U[report.f]?.n || "Người dùng")}`);
        }).join("")
      : '<div class="empty">Không có báo cáo nào cần xử lý.</div>';
  } else {
    content += all.length
      ? all.map(item => rowA(item, stB(item))).join("")
      : '<div class="empty">Chưa có tin đăng.</div>';
  }
  return content + "</div>";
}
async function setSt(id, status) {
  try {
    await api(`/moderation/listings/${id}/approve`, { method: "POST" });
    toast("Đã duyệt tin. Tin sẽ hiển thị cho người mua.");
    await render();
  } catch (error) {
    toast(error.message || "Không thể duyệt tin.");
  }
}
function askReason(id) {
  const item = L.find(listing => listing.id === id);
  if (!item) return;
  $("#dlg").innerHTML = `<div class="dh">Từ chối tin<button aria-label="Đóng" onclick="$('#dlg').close()">×</button></div>
    <div class="db"><div><b>${esc(item.t)}</b><div class="mut">Người bán: ${esc(U[item.s]?.n || "Người bán")}</div></div>
    <label class="f" id="rjf">Lý do từ chối *<textarea id="rj" rows="3" maxlength="500"></textarea><span class="err"></span></label>
    <div class="row"><button class="btn o" style="flex:1" onclick="$('#dlg').close()">Hủy</button>
    <button class="btn r" style="flex:1" onclick="doReject(${id})">Xác nhận từ chối</button></div></div>`;
  $("#dlg").showModal();
}
async function doReject(id) {
  const reason = $("#rj").value.trim();
  const field = $("#rjf");
  field.classList.remove("bad");
  field.querySelector(".err").textContent = "";
  if (reason.length < 5) {
    field.classList.add("bad");
    field.querySelector(".err").textContent = "Lý do cần ít nhất 5 ký tự.";
    return;
  }
  try {
    await api(`/moderation/listings/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason })
    });
    $("#dlg").close();
    toast("Đã từ chối tin và lưu lý do.");
    await render();
  } catch (error) {
    toast(error.message || "Không thể từ chối tin.");
  }
}
async function resolve(id, hide) {
  try {
    await api(`/moderation/reports/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        action: hide ? "hide_listing" : "dismiss",
        note: hide ? "Đã xác nhận vi phạm và ẩn tin." : "Báo cáo đã được kiểm tra và bỏ qua."
      })
    });
    toast(hide ? "Đã ẩn tin vi phạm." : "Đã bỏ qua báo cáo.");
    await render();
  } catch (error) {
    toast(error.message || "Không thể xử lý báo cáo.");
  }
}
function view(id) {
  const item = L.find(listing => listing.id === id);
  if (!item) return;
  const images = item.im?.length
    ? item.im.map(url => `<img src="${url}" alt="" style="max-width:100%;border-radius:10px;margin:4px 0">`).join("")
    : '<div class="tile"><span>📦</span></div>';
  $("#dlg").innerHTML = `<div class="dh">${esc(item.t)}<button aria-label="Đóng" onclick="$('#dlg').close()">×</button></div>
    <div class="db">${images}<div class="pr" style="font-size:22px">${vnd(item.p)}</div>
    <div class="mut">${stB(item)} · ${esc(U[item.s]?.n || "Người bán")}</div>
    <p>${esc(item.ds)}</p>${item.rr ? `<div class="mut">Lý do từ chối: ${esc(item.rr)}</div>` : ""}</div>`;
  $("#dlg").showModal();
}
async function render() {
  $("#who").innerHTML = ADM()
    ? '<span class="wn">Kiểm duyệt viên</span><button class="btn o sm" onclick="logout();render()">Đăng xuất</button>'
    : "";
  if (!ADM()) {
    $("#app").innerHTML = loginHtml();
    return;
  }
  $("#app").innerHTML = '<div class="card pad">Đang tải dữ liệu từ máy chủ...</div>';
  try {
    await loadModerationData();
    $("#app").innerHTML = dash();
  } catch (error) {
    console.error("Không tải được dữ liệu kiểm duyệt:", error);
    L = [];
    RP = [];
    $("#app").innerHTML = `<div class="card pad"><b>Không tải được dữ liệu từ Backend.</b><p class="mut">${esc(error.message)}</p><button class="btn" onclick="render()">Thử lại</button></div>`;
  }
}
$("#dlg").addEventListener("click", event => {
  if (event.target.id === "dlg") event.target.close();
});
addEventListener("storage", event => {
  if (["cdcsv_token", "cdcsv_buser", "cdcsv_admin"].includes(event.key)) render();
});

render();
