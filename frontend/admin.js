
/* ==========================================
   TRANG QUẢN TRỊ - KIỂM DUYỆT TIN
   Dùng chung dữ liệu với trang chợ qua data.js
========================================== */

const ADM = () => sessionStorage.getItem(AKEY) === '1' && !!sessionStorage.getItem(AUTH_TOKEN_KEY);

let tab = 'pending';

getUsers().forEach(u => {
    U[u.id] = {
        n: u.name,
        h: '@' + u.email.split('@')[0]
    };
});

const un = id => U[id] ? U[id].n : 'Người dùng';


/* Thông báo */
function toast(m) {
    const t = $('#toast');

    t.textContent = m;
    t.style.display = 'block';

    clearTimeout(toast.h);

    toast.h = setTimeout(() => {
        t.style.display = 'none';
    }, 3000);
}


/* Trạng thái tin */
const stB = l => ({
    pending: '<span class="badge w">Chờ duyệt</span>',
    approved: '<span class="badge">Đang bán</span>',
    sold: '<span class="badge">Đã bán</span>',
    hidden: '<span class="badge x">Bị ẩn</span>'
}[l.st] || '');


/* Ảnh tin */
const tl = l => `
    <div class="tile" style="--h:${l.id * 47 % 360}">
        ${l.im
            ? `<img src="${l.im[0]}" alt="">`
            : `<span>${l.e}</span>`
        }
    </div>
`;


/* Một dòng tin */
function rowA(l, acts, sub = '') {
    return `
        <div class="ls">
            ${tl(l)}

            <div class="gr" onclick="view(${l.id})">
                <b>${esc(l.t)}</b>

                <span class="mut">
                    ${vnd(l.p)}
                    · ${esc(un(l.s))}
                    · ${ago(l.a)}
                    ${sub}
                </span>
            </div>

            <div class="acts">
                ${acts}
            </div>
        </div>
    `;
}


/* Kiểm tra đăng nhập */
function render() {
    loadData();

    $('#who').innerHTML = ADM()
        ? `
            <span class="wn">Kiểm duyệt viên</span>
            <button class="btn o sm"
                onclick="adminLogout();render()">
                Đăng xuất
            </button>
        `
        : '';

    $('#app').innerHTML = ADM()
        ? dash()
        : loginHtml();
}


/* Form đăng nhập */
function loginHtml() {
    return `
        <div class="card pad"
             style="max-width:420px;margin:40px auto">

            <div class="sh">
                <span>🛡️</span>
                Đăng nhập quản trị
            </div>

            <div class="db" style="padding:0">

                <label class="f">
                    Email
                    <input
                        id="ae"
                        type="email"
                        autocomplete="username"
                    >
                </label>

                <label class="f">
                    Mật khẩu
                    <input
                        id="ap"
                        type="password"
                        autocomplete="current-password"
                        onkeydown="if(event.key==='Enter')adminIn()"
                    >
                </label>

                <span class="err" id="aer"></span>

                <button class="btn" onclick="adminIn()">
                    Đăng nhập
                </button>

                <a href="index.html" class="mut">
                    ← Về trang chợ sinh viên
                </a>

            </div>
        </div>
    `;
}


/* Đăng nhập admin và moderator */
async function adminIn() {
    const email = $('#ae').value.trim();
    const password = $('#ap').value;

    const error = $('#aer');

    error.textContent = '';

    if (!email || !password) {
        error.textContent = 'Vui lòng nhập email và mật khẩu.';
        return;
    }


    // Không giữ quyền quản trị cũ
    sessionStorage.removeItem(AKEY);

    const btn = document.querySelector('#app button.btn');

    if (btn) btn.disabled = true;

    try {
        // Đăng nhập bằng backend FastAPI
        const result = await login(email, password);

        if (!result.ok) {
            error.textContent =
                result.msg || 'Email hoặc mật khẩu không đúng.';
            return;
        }

        const role = String(result.role || '').toLowerCase();

        if (
            role === 'admin' ||
            role === 'moderator' ||
            role.startsWith('mod')
        ) {
            sessionStorage.setItem(AKEY, '1');
            render();
        } else {
            sessionStorage.removeItem(AKEY);

            error.textContent =
                'Tài khoản này không có quyền quản trị hoặc kiểm duyệt.';
        }

    } catch (e) {
        console.error(e);

        error.textContent =
            'Có lỗi khi kết nối hệ thống. Hãy kiểm tra backend.';
    } finally {
        if (btn) btn.disabled = false;
    }
}


/* Bảng quản trị */
function dash() {
    const P = L.filter(l => l.st === 'pending');
    const Rp = RP.filter(x => x.open);
    const A = L.filter(l => l.st !== 'pending');

    const T = [
        ['pending', `Tin chờ duyệt (${P.length})`],
        ['reports', `Báo cáo vi phạm (${Rp.length})`],
        ['all', `Tất cả tin (${A.length})`]
    ];

    let h = `
        <div class="card tabs">
            ${T.map(t => `
                <button
                    class="tab ${tab === t[0] ? 'on' : ''}"
                    onclick="tab='${t[0]}';render()">
                    ${t[1]}
                </button>
            `).join('')}
        </div>

        <div class="card">
    `;

    // Tin chờ duyệt
    if (tab === 'pending') {
        h += P.length
            ? P.map(l => rowA(
                l,
                `
                    <button class="btn sm"
                        onclick="setSt(${l.id},'approved')">
                        Duyệt
                    </button>

                    <button class="btn sm r"
                        onclick="setSt(${l.id},'hidden')">
                        Từ chối
                    </button>
                `
            )).join('')
            : '<div class="empty">Không còn tin nào chờ duyệt.</div>';
    }

    // Báo cáo vi phạm
    if (tab === 'reports') {
        h += Rp.length
            ? Rp.map(x => {
                const l = L.find(y => y.id === x.l);

                if (!l) return '';

                return rowA(
                    l,
                    `
                        <button class="btn sm r"
                            onclick="resolve(${x.id},true)">
                            Ẩn tin
                        </button>

                        <button class="btn sm o"
                            onclick="resolve(${x.id},false)">
                            Bỏ qua
                        </button>
                    `,
                    ` · Lý do: ${esc(x.x)} (${esc(un(x.f))})`
                );
            }).join('')
            : '<div class="empty">Không có báo cáo nào.</div>';
    }

    // Tất cả tin
    if (tab === 'all') {
        h += A.map(l => rowA(
            l,
            `
                ${stB(l)}

                ${l.st === 'approved'
                    ? `<button class="btn sm r"
                        onclick="setSt(${l.id},'hidden')">
                        Ẩn
                       </button>`
                    : ''
                }

                ${l.st === 'hidden'
                    ? `<button class="btn sm o"
                        onclick="setSt(${l.id},'approved')">
                        Khôi phục
                       </button>`
                    : ''
                }
            `
        )).join('');
    }

    return h + '</div>';
}


/* Cập nhật trạng thái tin gốc */
function setStOriginal(id, st) {
    const l = L.find(x => x.id === id);

    if (!l) return;

    const prev = l.st;

    l.st = st;

    if (st === 'approved') {
        notify(
            l.s,
            prev === 'pending'
                ? `Tin "${l.t}" đã được duyệt và hiển thị cho mọi người`
                : `Tin "${l.t}" đã được khôi phục`,
            'mine',
            prev === 'pending' ? '🎉' : '↩️'
        );
    }

    if (st === 'hidden') {
        notify(
            l.s,
            prev === 'pending'
                ? `Tin "${l.t}" không được duyệt`
                : `Tin "${l.t}" đã bị kiểm duyệt viên ẩn`,
            'mine',
            '⚠️'
        );
    }

    saveData();

    toast(
        st === 'approved'
            ? 'Đã duyệt. Tin đã hiển thị cho mọi người.'
            : st === 'hidden'
                ? 'Đã ẩn tin.'
                : 'Đã cập nhật.'
    );

    render();
}


/* Ẩn tin phải nhập lý do */
function setSt(id, st) {
    const l = L.find(x => x.id === id);

    if (!l) return;

    if (st === 'hidden') {
        askReason(id);
        return;
    }

    if (st === 'approved') {
        delete l.rr;
    }

    setStOriginal(id, st);
}


/* Form nhập lý do */
function askReason(id) {
    const l = L.find(x => x.id === id);

    if (!l) return;

    const pend = l.st === 'pending';

    $('#dlg').innerHTML = `
        <div class="dh">
            ${pend ? 'Từ chối tin' : 'Ẩn tin'}

            <button aria-label="Đóng"
                onclick="$('#dlg').close()">
                ×
            </button>
        </div>

        <div class="db">

            <div>
                <b>${esc(l.t)}</b>
                <div class="mut">
                    Người bán: ${esc(un(l.s))}
                </div>
            </div>

            <label class="f" id="rjf">
                Lý do ${pend ? 'từ chối' : 'ẩn'}
                (người bán sẽ nhìn thấy) *

                <textarea
                    id="rj"
                    rows="3"
                    maxlength="200"
                    placeholder="Ví dụ: Ảnh mờ, mô tả chưa đúng sản phẩm..."
                ></textarea>

                <span class="err"></span>
            </label>

            <div class="row">

                <button class="btn o"
                    style="flex:1"
                    onclick="$('#dlg').close()">
                    Hủy
                </button>

                <button class="btn r"
                    style="flex:1"
                    onclick="doReject(${id})">
                    ${pend ? 'Xác nhận từ chối' : 'Xác nhận ẩn'}
                </button>

            </div>
        </div>
    `;

    $('#dlg').showModal();
}


/* Xác nhận từ chối / ẩn tin */
function doReject(id) {
    const r = $('#rj').value.trim();
    const f = $('#rjf');

    f.classList.remove('bad');
    f.querySelector('.err').textContent = '';

    if (r.length < 5) {
        f.classList.add('bad');

        f.querySelector('.err').textContent =
            'Vui lòng nhập lý do (ít nhất 5 ký tự).';

        return;
    }

    const l = L.find(x => x.id === id);

    if (!l) return;

    l.rr = r;

    // Cập nhật trạng thái và lưu dữ liệu
    setStOriginal(id, 'hidden');

    // Bổ sung lý do vào thông báo vừa tạo
    const last = NOTI[NOTI.length - 1];

    if (last && last.to === l.s) {
        last.t += ' Lý do: ' + r;
    }

    saveData();

    $('#dlg').close();
}


/* Xử lý báo cáo */
function resolve(id, hide) {
    const r = RP.find(x => x.id === id);

    if (!r) return;

    r.open = false;

    if (hide) {
        const l = L.find(y => y.id === r.l);

        if (l) {
            l.st = 'hidden';

            notify(
                l.s,
                `Tin "${l.t}" đã bị ẩn do bị báo cáo vi phạm`,
                'mine',
                '⚠️'
            );
        }
    }

    saveData();

    toast(
        hide
            ? 'Đã ẩn tin vi phạm.'
            : 'Đã bỏ qua báo cáo.'
    );

    render();
}


/* Xem chi tiết tin */
function view(id) {
    const l = L.find(x => x.id === id);

    if (!l) return;

    $('#dlg').innerHTML = `
        <div class="dh">
            ${esc(l.t)}

            <button aria-label="Đóng"
                onclick="$('#dlg').close()">
                ×
            </button>
        </div>

        <div class="db">

            <div class="gal"
                style="--h:${l.id * 47 % 360}">

                ${l.im
                    ? `<img src="${l.im[0]}" alt="">`
                    : `<span>${l.e}</span>`
                }

                <b class="cnt">${l.n} ảnh</b>
            </div>

            <div>
                <div class="pr" style="font-size:22px">
                    ${vnd(l.p)}
                </div>

                <div class="mut">
                    ${stB(l)}
                    ${CATS[l.c][0]}
                    · ${CONDS[l.k]}
                    · ${ago(l.a)}
                </div>
            </div>

            <p style="margin:0">
                ${esc(l.ds)}
            </p>

            <div class="mut">
                Người bán: ${esc(un(l.s))}
            </div>

            ${l.rr
                ? `<div class="mut">
                    Lý do kiểm duyệt: ${esc(l.rr)}
                   </div>`
                : ''
            }

        </div>
    `;

    $('#dlg').showModal();
}


/* Đóng hộp thoại khi bấm bên ngoài */
$('#dlg').addEventListener('click', e => {
    if (e.target.id === 'dlg') {
        e.target.close();
    }
});


/* Cập nhật khi dữ liệu thay đổi ở tab khác */
addEventListener('storage', e => {
    if (
        e.key === KEY ||
        e.key === UKEY ||
        e.key === AKEY
    ) {
        render();
    }
});


/* Thống kê đầu trang */
const _dash = dash;

dash = function () {
    RP = RP.filter(x =>
        L.some(l => l.id === x.l)
    );

    const c = s => L.filter(l => l.st === s).length;

    const box = (n, t) => `
        <div class="card pad" style="text-align:center">
            <div class="pr" style="font-size:24px">
                ${n}
            </div>

            <div class="mut">
                ${t}
            </div>
        </div>
    `;

    return `
        <div style="
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
            gap:12px;
            margin-bottom:12px
        ">
            ${box(c('pending'), 'Chờ duyệt')}
            ${box(c('approved'), 'Đang bán')}
            ${box(c('sold'), 'Đã bán')}
            ${box(c('hidden'), 'Bị ẩn')}
            ${box(RP.filter(x => x.open).length, 'Báo cáo mở')}
        </div>
    ` + _dash();
};


/* Khởi chạy */
render();



/* ===== ADMIN DÙNG DỮ LIỆU TỪ BACKEND ===== */
let admCats = [], admState = 0;   // admState: 0 chưa tải, 1 đang tải, 2 xong
const isAdm = () => sessionStorage.getItem(AKEY) === '1' && !!sessionStorage.getItem(AUTH_TOKEN_KEY);

adminLogin = () => false;          // bỏ tài khoản cứng: bắt buộc đăng nhập qua backend
adminLogout = function () { logout(); admState = 0; };

async function admFetch(path, opt = {}) {
  const h = { Authorization: 'Bearer ' + sessionStorage.getItem(AUTH_TOKEN_KEY) };
  if (opt.body) h['Content-Type'] = 'application/json';
  const res = await fetch(AUTH_API_BASE + path, { ...opt, headers: h });
  const data = await res.json().catch(() => null);
  if (res.status === 401) {
    sessionStorage.removeItem(AKEY); sessionStorage.removeItem(AUTH_TOKEN_KEY);
    throw new Error('Phiên đăng nhập hết hạn, hãy đăng nhập lại.');
  }
  if (!res.ok) throw new Error((data && data.error && data.error.message) || ('Lỗi ' + res.status));
  return data;
}

const ADM_COND = { like_new: 0, good: 1, fair: 2 };
function admMap(x) {
  const p = x.thumbnail_url || (x.images && x.images[0] && (x.images[0].url || x.images[0].image_url));
  const origin = AUTH_API_BASE.replace('/api/v1', '');
  return {
    id: x.id, t: x.title, p: x.price,
    c: Math.max(0, admCats.indexOf(x.category && x.category.id)),
    k: ADM_COND[x.condition] ?? 1,
    s: x.seller && x.seller.id,
    a: Math.max(0, Math.floor((Date.now() - new Date(x.created_at || Date.now())) / 864e5)),
    n: (x.images && x.images.length) || 1,
    im: p ? [p.startsWith('http') ? p : origin + p] : null,
    st: x.status === 'rejected' ? 'hidden' : x.status,
    rr: x.reject_reason || '',
    e: '📦', ds: x.description || ''
  };
}

async function admLoad() {
  try {
    const rc = await admFetch('/categories');
    const cats = Array.isArray(rc) ? rc : rc.items;
    admCats = cats.map(c => c.id);
    CATS.length = 0; cats.forEach(c => CATS.push([c.name, '📦']));
    const all = [];
    for (const st of ['pending', 'approved', 'sold', 'hidden', 'rejected']) {
      const r = await admFetch('/moderation/listings?status=' + st + '&page_size=100');
      (r.items || []).forEach(x => {
        all.push(admMap(x));
        if (x.seller) U[x.seller.id] = { n: x.seller.full_name, h: '' };
      });
    }
    L = all;
    const reports = await admFetch('/moderation/reports?status=open&page_size=100');
    RP = (reports.items || []).map(x => {
      if (x.reporter) U[x.reporter.id] = { n: x.reporter.full_name, h: '' };
      if (x.listing && x.listing.seller) U[x.listing.seller.id] = { n: x.listing.seller.full_name, h: '' };
      return { id: x.id, l: x.listing.id, f: x.reporter.id, x: x.detail || x.reason_code, open: x.status === 'open' };
    });
  } catch (e) { toast(e.message); }
  admState = 2; render();
}

render = function () {
  const on = isAdm();
  $('#who').innerHTML = on
    ? `<span class="wn">Kiểm duyệt viên</span><button class="btn o sm" onclick="adminLogout();render()">Đăng xuất</button>`
    : '';
  if (!on) { admState = 0; $('#app').innerHTML = loginHtml(); return; }
  if (admState === 0) { admState = 1; admLoad(); }
  $('#app').innerHTML = admState === 2 ? dash() : '<div class="card empty">Đang tải dữ liệu từ máy chủ...</div>';
};

async function admAct(path, body, okMsg) {
  try {
    await admFetch(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined });
    toast(okMsg);
  } catch (e) { toast(e.message); }
  admState = 0; render();
}

resolve = async function (id, hide) {
  const note = hide ? 'Đã xác nhận vi phạm và ẩn tin đăng.' : 'Báo cáo đã được kiểm tra và bỏ qua.';
  try {
    await admFetch('/moderation/reports/' + id, {
      method: 'PATCH',
      body: JSON.stringify({ action: hide ? 'hide_listing' : 'dismiss', note })
    });
    toast(hide ? 'Đã ẩn tin vi phạm.' : 'Đã bỏ qua báo cáo.');
  } catch (e) { toast(e.message); }
  admState = 0;
  render();
};

setSt = function (id, st) {
  const l = L.find(x => x.id === id);
  if (!l) return;
  if (st === 'hidden') {
    if (l.st === 'pending') return askReason(id);
    return toast('Backend chưa hỗ trợ ẩn tin đang bán ở mục này.');
  }
  if (st === 'approved') {
    if (l.st !== 'pending') return toast('Backend chỉ cho duyệt tin đang chờ duyệt.');
    admAct('/moderation/listings/' + id + '/approve', null, 'Đã duyệt. Tin đã hiển thị cho mọi người.');
  }
};

doReject = function (id) {
  const r = $('#rj').value.trim(), f = $('#rjf');
  f.classList.remove('bad'); f.querySelector('.err').textContent = '';
  if (r.length < 5) {
    f.classList.add('bad');
    f.querySelector('.err').textContent = 'Vui lòng nhập lý do (ít nhất 5 ký tự).';
    return;
  }
  $('#dlg').close();
  admAct('/moderation/listings/' + id + '/reject', { reason: r }, 'Đã từ chối tin.');
};

render();

/* ===== TỰ LÀM MỚI DANH SÁCH ===== */
let admBusy = false;
async function admRefresh() {
  if (!isAdm() || admState !== 2 || admBusy) return;
  const d = $('#dlg');
  if (d && d.open) return;          // đang mở hộp thoại thì không làm mới
  admBusy = true;
  try { await admLoad(); } finally { admBusy = false; }
}
setInterval(admRefresh, 10000);      // 10 giây làm mới một lần
addEventListener('focus', admRefresh);   // quay lại tab admin là làm mới ngay
document.addEventListener('visibilitychange', () => { if (!document.hidden) admRefresh(); });