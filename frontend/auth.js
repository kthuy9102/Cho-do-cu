/* Xác thực tập trung qua FastAPI. Không xác thực giả bằng localStorage. */
const UKEY = "cdcsv_users";
const SKEY = "cdcsv_session";
const AKEY = "cdcsv_admin";
const GOOGLE_CLIENT_ID = "";
const AUTH_API_ORIGIN = location.port === "5500"
  ? `${location.protocol}//${location.hostname}:8001`
  : "";
const AUTH_API = AUTH_API_ORIGIN + "/api/v1";
const AUTH_TOKEN_KEY = "cdcsv_token";
const AUTH_BUSER_KEY = "cdcsv_buser";

function getUsers() {
  try { return JSON.parse(localStorage.getItem(UKEY) || "[]"); }
  catch { return []; }
}
function putUsers(users) {
  localStorage.setItem(UKEY, JSON.stringify(users));
}
function session() {
  try {
    const user = localStorage.getItem(AUTH_BUSER_KEY);
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    return user && token ? JSON.parse(user) : null;
  } catch {
    return null;
  }
}
function logout() {
  [SKEY, AUTH_TOKEN_KEY, AUTH_BUSER_KEY, AKEY].forEach(key => localStorage.removeItem(key));
}
function authBearerHeader() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  return token ? { Authorization: "Bearer " + token } : {};
}

function apiErrorMessage(data, fallback) {
  return data?.error?.message || data?.detail || fallback;
}

async function register(values) {
  const errors = {};
  const name = (values.name || "").trim();
  const email = (values.email || "").trim().toLowerCase();
  const studentId = (values.mssv || "").trim();
  const phone = (values.phone || "").replace(/\\s/g, "");

  if (name.length < 2) errors.name = "Nhập họ và tên (ít nhất 2 ký tự).";
  if (!/^[A-Za-z0-9]{6,12}$/.test(studentId)) errors.mssv = "MSSV gồm 6–12 chữ hoặc số.";
  if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) errors.email = "Email không hợp lệ.";
  if (phone && !/^(0|\\+84)\\d{9}$/.test(phone)) errors.phone = "Số điện thoại không hợp lệ.";
  if (!values.pw || values.pw.length < 8 || !/[A-Za-z]/.test(values.pw) || !/\\d/.test(values.pw)) {
    errors.pw = "Mật khẩu ít nhất 8 ký tự, gồm cả chữ và số.";
  }
  if (values.pw2 !== values.pw) errors.pw2 = "Mật khẩu nhập lại không khớp.";
  if (!values.agree) errors.agree = "Bạn cần đồng ý với điều khoản.";
  if (Object.keys(errors).length) return { ok: false, errors };

  let response;
  try {
    response = await fetch(AUTH_API + "/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password: values.pw,
        full_name: name,
        student_id: studentId
      })
    });
  } catch {
    return { ok: false, errors: { email: "Không kết nối được Backend. Kiểm tra API tại cổng 8001." } };
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = apiErrorMessage(data, "Không thể tạo tài khoản.");
    return { ok: false, errors: { email: message } };
  }

  // API đăng ký không tự cấp token: đăng nhập ngay bằng tài khoản vừa tạo.
  const loginResult = await login(email, values.pw);
  if (!loginResult.ok) {
    return { ok: false, errors: { pw: "Tạo tài khoản thành công nhưng đăng nhập tự động thất bại. Hãy đăng nhập lại." } };
  }
  return { ok: true, role: loginResult.role };
}

async function authFetchMe(token) {
  try {
    const response = await fetch(AUTH_API + "/users/me", {
      headers: { Authorization: "Bearer " + token }
    });
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

async function login(email, password) {
  if (!email) return { ok: false, field: "email", msg: "Nhập email." };
  if (!password) return { ok: false, field: "pw", msg: "Nhập mật khẩu." };

  email = email.trim().toLowerCase();
  let response;
  try {
    response = await fetch(AUTH_API + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password })
    });
  } catch (error) {
    console.error("Không kết nối được Backend:", error);
    return { ok: false, field: "pw", msg: "Không kết nối được máy chủ. Kiểm tra Backend và thử lại." };
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    console.warn("Backend trả về", response.status, data);
    return { ok: false, field: "pw", msg: apiErrorMessage(data, "Email hoặc mật khẩu không đúng.") };
  }

  if (!data.access_token || !data.user) {
    console.error("Phản hồi login thiếu access_token hoặc user:", data);
    return { ok: false, field: "pw", msg: "Phản hồi đăng nhập từ máy chủ không hợp lệ." };
  }

  const user = data.user;
  const role = String(user.role || "student").toLowerCase();
  const browserUser = {
    id: user.id,
    name: user.full_name || email.split("@")[0],
    email: user.email || email,
    mssv: user.student_id || "",
    phone: "",
    role,
    backend: true
  };

  localStorage.removeItem(SKEY);
  localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
  localStorage.setItem(AUTH_BUSER_KEY, JSON.stringify(browserUser));
  if (role === "admin" || role === "moderator") localStorage.setItem(AKEY, "1");
  else localStorage.removeItem(AKEY);
  return { ok: true, role };
}

/* Tắt các luồng đăng nhập giả; Google OAuth cần được xác minh ở Backend trước khi bật. */
async function authLoginLocal() {
  return { ok: false, msg: "Đăng nhập tài khoản demo trên trình duyệt đã bị tắt. Hãy dùng tài khoản Backend." };
}
async function loginGoogle() {
  return { ok: false, msg: "Đăng nhập Google chưa được cấu hình xác thực phía Backend." };
}
function decodeJwt(token) {
  const part = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(decodeURIComponent(escape(atob(part))));
}
function adminLogin() { return false; }
function adminLogout() { localStorage.removeItem(AKEY); }
