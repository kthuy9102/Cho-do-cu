/* Frontend chỉ giữ cấu trúc dữ liệu rỗng; danh mục, tin đăng và giao dịch được tải từ FastAPI. */
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? "").replace(/[&<>"]/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"
})[char]);
const nz = value => String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").toLowerCase();
const vnd = amount => Number(amount || 0).toLocaleString("vi-VN") + "đ";
const ago = days => days < 1 ? "Hôm nay" : days < 7 ? days + " ngày trước" : days < 30 ? Math.floor(days / 7) + " tuần trước" : Math.floor(days / 30) + " tháng trước";

const CATS = [];
const CONDS = ["Mới 99%", "Đã dùng, còn tốt", "Cũ, dùng được"];
const U = {};
let L = [];
let O = [];
let R = [];
let RP = [];
let ORD = [];
let NOTI = [];

function notify(to, title, link, icon) {
  NOTI.push({
    id: NOTI.length ? Math.max(...NOTI.map(item => item.id)) + 1 : 1,
    to, t: title, link: link || "home", ic: icon || "🔔",
    ts: Date.now(), read: false
  });
}
const KEY = "cdcsv_v2";
function loadData() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || "null");
    NOTI = Array.isArray(saved?.NOTI) ? saved.NOTI : [];
  } catch {
    NOTI = [];
  }
}
function saveData() {
  try {
    localStorage.setItem(KEY, JSON.stringify({ NOTI }));
    return true;
  } catch {
    return false;
  }
}
function resetData() {
  localStorage.removeItem(KEY);
  location.reload();
}
loadData();
