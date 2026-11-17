/* =========================
   XÁC THỰC TÀI KHOẢN
   Backend FastAPI (không dùng xác thực local)
   Đăng nhập lưu bằng sessionStorage => mỗi tab giữ tài khoản riêng
========================= */

const UKEY = 'cdcsv_users';
const SKEY = 'cdcsv_session';
const AKEY = 'cdcsv_admin';

const GOOGLE_CLIENT_ID = '';

const ADMIN = {
    email: 'admin@example.com',
    pw: 'Admin12345'
};

const AUTH_API = '/api/v1';
const AUTH_API_BASE = ['5000', '5500'].includes(location.port) ? 'http://localhost:8001' + AUTH_API : AUTH_API;
const AUTH_TOKEN_KEY = 'cdcsv_token';
const AUTH_BUSER_KEY = 'cdcsv_buser';


/* Mã hóa mật khẩu */
async function sha(p) {
    try {
        const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('cdcsv:' + p));
        return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
    } catch (e) {
        let h = 5381;
        for (const c of 'cdcsv:' + p) h = (h * 33 ^ c.charCodeAt(0)) >>> 0;
        return 'x' + h;
    }
}


/* Danh sách tài khoản local (dùng chung mọi tab) */
function getUsers() {
    try { return JSON.parse(localStorage.getItem(UKEY) || '[]'); }
    catch (e) { return []; }
}

function putUsers(a) {
    localStorage.setItem(UKEY, JSON.stringify(a));
}


/* Tạo tài khoản demo */
async function seedUsers() {
    if (getUsers().length) return;

    const h = await sha('123456');

    putUsers([
        ['u1', 'Nguyễn Văn An', 'an@demo.vn', 'SV0001'],
        ['u2', 'Minh Anh', 'minhanh@demo.vn', 'SV0002'],
        ['u3', 'Hoàng Long', 'long@demo.vn', 'SV0003'],
        ['u4', 'Thu Hà', 'ha@demo.vn', 'SV0004']
    ].map(([id, name, email, mssv]) => ({
        id, name, email, mssv, phone: '0900000000', pw: h
    })));
}


/* Lấy phiên đăng nhập (riêng từng tab) */
function session() {
    try {
        const b = sessionStorage.getItem(AUTH_BUSER_KEY);
        return b && sessionStorage.getItem(AUTH_TOKEN_KEY) ? JSON.parse(b) : null;
    } catch (e) {
        return null;
    }
}


/* Đăng xuất */
function logout() {
    [SKEY, AUTH_TOKEN_KEY, AUTH_BUSER_KEY, AKEY].forEach(k => sessionStorage.removeItem(k));
}


/* Header xác thực */
function authBearerHeader() {
    const t = sessionStorage.getItem(AUTH_TOKEN_KEY);
    return t ? { Authorization: 'Bearer ' + t } : {};
}


/* Đăng nhập local dự phòng */
async function authLoginLocal() {
    return { ok: false, msg: 'Đăng nhập local đã bị tắt. Vui lòng sử dụng tài khoản trên máy chủ.' };
}


/* Giải mã JWT */
function decodeJwt(t) {
    try {
        const b = t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(decodeURIComponent(escape(atob(b))));
    } catch (e) {
        return {};
    }
}


/* Lấy thông tin người dùng từ backend */
async function authFetchMe(tk) {
    const r = await fetch(AUTH_API_BASE + '/users/me', {
        headers: { Authorization: 'Bearer ' + tk }
    });
    if (!r.ok) throw new Error('Không lấy được hồ sơ tài khoản (HTTP ' + r.status + ').');
    return r.json();
}


/* Đăng nhập backend */
async function login(email, pw) {
    if (!email) return { ok: false, field: 'email', msg: 'Nhập email.' };
    if (!pw) return { ok: false, field: 'pw', msg: 'Nhập mật khẩu.' };

    email = email.trim().toLowerCase();

    let res;

    try {
        res = await fetch(AUTH_API_BASE + '/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username: email, password: pw })
        });
    } catch (e) {
        console.warn('Không kết nối được backend:', e);
        return { ok: false, field: 'pw', msg: 'Không kết nối được máy chủ. Không thể đăng nhập khi Backend ngoại tuyến.' };
    }

    if (!res.ok) {
        const detail = await res.text();
        console.warn('Backend trả về:', res.status, detail);
        return {
            ok: false,
            field: 'pw',
            msg: res.status === 401
                ? 'Email hoặc mật khẩu không đúng.'
                : 'Đăng nhập thất bại (HTTP ' + res.status + ').'
        };
    }

    try {
        const data = await res.json();
        const access_token = data.access_token;

        if (!access_token) {
            return { ok: false, msg: 'Backend không trả về access_token.' };
        }

        sessionStorage.setItem(AUTH_TOKEN_KEY, access_token);
        sessionStorage.removeItem(SKEY);

        const me = await authFetchMe(access_token);
        const claims = decodeJwt(access_token);

        const role = String(
            me.role || me.user?.role || claims.role || claims.role_name || 'student'
        ).toLowerCase();

        const u = {
            id: me.id ?? me.user?.id ?? claims.sub ?? email,
            name: me.full_name || me.name || me.user?.full_name || email.split('@')[0],
            email: me.email || me.user?.email || email,
            mssv: me.student_id || me.mssv || '',
            phone: me.phone || '',
            role,
            backend: true
        };

        sessionStorage.setItem(AUTH_BUSER_KEY, JSON.stringify(u));

        if (role === 'admin' || role.startsWith('mod')) {
            sessionStorage.setItem(AKEY, '1');
        } else {
            sessionStorage.removeItem(AKEY);
        }

        return { ok: true, role };

    } catch (e) {
        console.error('Lỗi xử lý đăng nhập:', e);
        sessionStorage.removeItem(AUTH_TOKEN_KEY);
        sessionStorage.removeItem(AUTH_BUSER_KEY);
        sessionStorage.removeItem(AKEY);
        return { ok: false, msg: e.message || 'Không đọc được dữ liệu đăng nhập từ backend.' };
    }
}


/* Đăng ký: lưu vào backend rồi đăng nhập luôn */
async function register(v) {
    const e = {};
    const name = (v.name || '').trim();
    const email = (v.email || '').trim().toLowerCase();
    const mssv = (v.mssv || '').trim();
    const phone = (v.phone || '').replace(/\s/g, '');

    if (name.length < 2) e.name = 'Nhập họ và tên (ít nhất 2 ký tự).';
    if (!/^[A-Za-z0-9]{6,12}$/.test(mssv)) e.mssv = 'MSSV gồm 6–12 chữ hoặc số.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = 'Email không hợp lệ.';
    if (!/^(0|\+84)\d{9}$/.test(phone)) e.phone = 'Số điện thoại không hợp lệ.';
    if (!v.pw || v.pw.length < 8 || !/[A-Za-z]/.test(v.pw) || !/\d/.test(v.pw)) e.pw = 'Mật khẩu ít nhất 8 ký tự, gồm cả chữ và số.';
    if (v.pw2 !== v.pw) e.pw2 = 'Mật khẩu nhập lại không khớp.';
    if (!v.agree) e.agree = 'Bạn cần đồng ý với điều khoản.';
    if (Object.keys(e).length) return { ok: false, errors: e };

    const send = body => fetch(AUTH_API_BASE + '/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const base = { email, password: v.pw, full_name: name, student_id: mssv };
    let res, data;

    try {
        res = await send({ ...base, phone });
        if (res.status === 422) res = await send(base);
        data = await res.json().catch(() => null);
    } catch (err) {
        return { ok: false, errors: { email: 'Không kết nối được máy chủ. Hãy kiểm tra backend.' } };
    }

    if (!res.ok) {
        const map = { full_name: 'name', student_id: 'mssv', password: 'pw', phone: 'phone', email: 'email' };
        const errs = {};
        const det = data && data.error && data.error.details;

        if (Array.isArray(det) && det.length) {
            det.forEach(d => {
                const key = map[Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : ''] || 'email';
                errs[key] = d.msg || d.message || 'Không hợp lệ.';
            });
        } else {
            errs.email = res.status === 409
                ? 'Email này đã được đăng ký.'
                : (data && data.error && data.error.message) || ('Đăng ký thất bại (mã ' + res.status + ').');
        }
        return { ok: false, errors: errs };
    }

    const r = await login(email, v.pw);
    return r.ok ? { ok: true } : { ok: false, errors: { email: r.msg || 'Đăng ký xong nhưng chưa đăng nhập được.' } };
}


/* Đăng nhập Google */
async function loginGoogle() {
    return { ok: false, msg: 'Đăng nhập Google chưa được cấu hình trên Backend.' };
}


/* Đăng nhập quản trị local dự phòng */
function adminLogin() {
    return false;
}


/* Đăng xuất quản trị */
function adminLogout() {
    sessionStorage.removeItem(AKEY);
}