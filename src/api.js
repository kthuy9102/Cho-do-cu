import axios from "axios";
const api = axios.create({ baseURL: "/api" });
api.interceptors.request.use(c => { const t = localStorage.getItem("token"); if (t) c.headers.Authorization = `Bearer ${t}`; return c; });
api.interceptors.response.use(r => r, e => {
  if (e.response?.status === 401 && !location.pathname.startsWith("/login")) {
    localStorage.removeItem("token"); localStorage.removeItem("user"); location.href = "/login";
  }
  return Promise.reject(e);
});
export const errMsg = e => { const d = e.response?.data?.detail; return Array.isArray(d) ? d.map(x => `${x.loc?.slice(-1)}: ${x.msg}`).join("; ") : d || "Không kết nối được máy chủ"; };
export const money = n => Number(n || 0).toLocaleString("vi-VN") + " đ";
export const STATUS = { pending: "Chờ duyệt", approved: "Đang bán", rejected: "Bị từ chối", sold: "Đã bán" };
export default api;
