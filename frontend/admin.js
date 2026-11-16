/* Trang quản trị dành riêng cho kiểm duyệt viên. Dùng chung dữ liệu với trang chợ qua data.js. */
const ADM=()=>{try{const u=JSON.parse(localStorage.getItem(AUTH_BUSER_KEY)||'null');return localStorage.getItem(AKEY)==='1'&&!!localStorage.getItem(AUTH_TOKEN_KEY)&&!!u&&['admin','moderator'].includes(String(u.role||'').trim().toLowerCase())}catch(e){return false}};
let tab='pending';
getUsers().forEach(u=>U[u.id]={n:u.name,h:'@'+u.email.split('@')[0]});
const un=id=>U[id]?U[id].n:'Người dùng';
function toast(m){const t=$('#toast');t.textContent=m;t.style.display='block';clearTimeout(toast.h);toast.h=setTimeout(()=>t.style.display='none',3000)}
const stB=l=>({pending:'<span class="badge w">Chờ duyệt</span>',approved:'<span class="badge">Đang bán</span>',sold:'<span class="badge">Đã bán</span>',hidden:'<span class="badge x">Bị ẩn</span>'}[l.st]);
const tl=l=>`<div class="tile" style="--h:${l.id*47%360}">${l.im?`<img src="${l.im[0]}" alt="">`:`<span>${l.e}</span>`}</div>`;
function rowA(l,acts,sub){return `<div class="ls">${tl(l)}<div class="gr" onclick="view(${l.id})"><b>${esc(l.t)}</b><span class="mut">${vnd(l.p)} · ${esc(un(l.s))} · ${ago(l.a)}${sub||''}</span></div><div class="acts">${acts}</div></div>`}

function render(){loadData();
  $('#who').innerHTML=ADM()?`<span class="wn">Kiểm duyệt viên</span><button class="btn o sm" onclick="adminLogout();render()">Đăng xuất</button>`:'';
  $('#app').innerHTML=ADM()?dash():loginHtml()}
function loginHtml(){return `<div class="card pad" style="max-width:420px;margin:40px auto"><div class="sh"><span>🛡️</span>Đăng nhập quản trị</div>
 <div class="db" style="padding:0"><label class="f">Email<input id="ae" type="email" autocomplete="username"></label>
 <label class="f">Mật khẩu<input id="ap" type="password" autocomplete="current-password" onkeydown="if(event.key==='Enter')adminIn()"></label>
 <span class="err" id="aer"></span><button class="btn" onclick="adminIn()">Đăng nhập</button>
 <a href="index.html" class="mut">← Về trang chợ sinh viên</a></div></div>`}
async function adminIn(){
  const email=$('#ae').value.trim().toLowerCase(), password=$('#ap').value;
  const btn=$('#app').querySelector('button.btn');
  const err=$('#aer');
  err.textContent='';
  if(btn)btn.disabled=true;
  try{
    const result=await login(email,password);
    if(!result.ok){
      err.textContent=result.msg||'Đăng nhập thất bại.';
      return;
    }
    const role=String(result.role||'').trim().toLowerCase();
    if(role!=='admin'&&role!=='moderator'){
      logout();
      err.textContent='Tài khoản này không có quyền quản trị.';
      return;
    }
    render();
  }catch(e){
    console.error('Lỗi đăng nhập quản trị:',e);
    err.textContent='Không thể đăng nhập. Vui lòng thử lại.';
  }finally{
    if(btn)btn.disabled=false;
  }
}
function dash(){const P=L.filter(l=>l.st==='pending'),Rp=RP.filter(x=>x.open),A=L.filter(l=>l.st!=='pending');
  const T=[['pending',`Tin chờ duyệt (${P.length})`],['reports',`Báo cáo vi phạm (${Rp.length})`],['all',`Tất cả tin (${A.length})`]];
  let h=`<div class="card tabs">${T.map(t=>`<button class="tab ${tab===t[0]?'on':''}" onclick="tab='${t[0]}';render()">${t[1]}</button>`).join('')}</div><div class="card">`;
  if(tab==='pending')h+=P.length?P.map(l=>rowA(l,`<button class="btn sm" onclick="setSt(${l.id},'approved')">Duyệt</button><button class="btn sm r" onclick="setSt(${l.id},'hidden')">Từ chối</button>`)).join(''):'<div class="empty">Không còn tin nào chờ duyệt.</div>';
  if(tab==='reports')h+=Rp.length?Rp.map(x=>{const l=L.find(y=>y.id===x.l);return rowA(l,`<button class="btn sm r" onclick="resolve(${x.id},true)">Ẩn tin</button><button class="btn sm o" onclick="resolve(${x.id},false)">Bỏ qua</button>`,` · Lý do: ${esc(x.x)} (${esc(un(x.f))})`)}).join(''):'<div class="empty">Không có báo cáo nào.</div>';
  if(tab==='all')h+=A.map(l=>rowA(l,`${stB(l)}${l.st==='approved'?`<button class="btn sm r" onclick="setSt(${l.id},'hidden')">Ẩn</button>`:l.st==='hidden'?`<button class="btn sm o" onclick="setSt(${l.id},'approved')">Khôi phục</button>`:''}`)).join('');
  return h+'</div>'}
function setSt(id,st){const l=L.find(x=>x.id===id),prev=l.st;l.st=st;
  if(st==='approved')notify(l.s,prev==='pending'?`Tin "${l.t}" đã được duyệt và hiển thị cho mọi người`:`Tin "${l.t}" đã được khôi phục`,'mine',prev==='pending'?'🎉':'↩️');
  if(st==='hidden')notify(l.s,prev==='pending'?`Tin "${l.t}" không được duyệt`:`Tin "${l.t}" đã bị kiểm duyệt viên ẩn`,'mine','⚠️');
  saveData();toast(st==='approved'?'Đã duyệt. Tin đã hiển thị cho mọi người.':st==='hidden'?'Đã ẩn tin.':'Đã cập nhật.');render()}
function resolve(id,hide){const r=RP.find(x=>x.id===id);r.open=false;
  if(hide){const l=L.find(y=>y.id===r.l);l.st='hidden';notify(l.s,`Tin "${l.t}" đã bị ẩn do bị báo cáo vi phạm`,'mine','⚠️')}
  saveData();toast(hide?'Đã ẩn tin vi phạm.':'Đã bỏ qua báo cáo.');render()}
function view(id){const l=L.find(x=>x.id===id);
  $('#dlg').innerHTML=`<div class="dh">${esc(l.t)}<button aria-label="Đóng" onclick="$('#dlg').close()">×</button></div><div class="db"><div class="gal" style="--h:${l.id*47%360}">${l.im?`<img src="${l.im[0]}" alt="">`:`<span>${l.e}</span>`}<b class="cnt">${l.n} ảnh</b></div>
  <div><div class="pr" style="font-size:22px">${vnd(l.p)}</div><div class="mut">${stB(l)} ${CATS[l.c][0]} · ${CONDS[l.k]} · ${ago(l.a)}</div></div><p style="margin:0">${esc(l.ds)}</p><div class="mut">Người bán: ${esc(un(l.s))}</div></div>`;
  $('#dlg').showModal()}
$('#dlg').addEventListener('click',e=>{if(e.target.id==='dlg')e.target.close()});
addEventListener('storage',e=>{if(e.key===KEY||e.key===UKEY||e.key===AKEY)render()});

/* ===== BỔ SUNG ===== */

/* 1. Từ chối / ẩn tin phải nhập lý do */
const _setSt = setSt;
setSt = function (id, st) {
  const l = L.find(x => x.id === id);
  if (st === 'hidden' && l) return askReason(id);
  if (st === 'approved' && l) delete l.rr;
  _setSt(id, st);
};
function askReason(id) {
  const l = L.find(x => x.id === id), pend = l.st === 'pending';
  $('#dlg').innerHTML = `<div class="dh">${pend ? 'Từ chối tin' : 'Ẩn tin'}<button aria-label="Đóng" onclick="$('#dlg').close()">×</button></div>
  <div class="db"><div><b>${esc(l.t)}</b><div class="mut">Người bán: ${esc(un(l.s))}</div></div>
  <label class="f" id="rjf">Lý do ${pend ? 'từ chối' : 'ẩn'} (người bán sẽ nhìn thấy) *
    <textarea id="rj" rows="3" maxlength="200" placeholder="Ví dụ: Ảnh mờ, mô tả chưa đúng sản phẩm..."></textarea><span class="err"></span></label>
  <div class="row"><button class="btn o" style="flex:1" onclick="$('#dlg').close()">Hủy</button>
  <button class="btn r" style="flex:1" onclick="doReject(${id})">${pend ? 'Xác nhận từ chối' : 'Xác nhận ẩn'}</button></div></div>`;
  $('#dlg').showModal();
}
function doReject(id) {
  const r = $('#rj').value.trim(), f = $('#rjf');
  f.classList.remove('bad'); f.querySelector('.err').textContent = '';
  if (r.length < 5) { f.classList.add('bad'); f.querySelector('.err').textContent = 'Vui lòng nhập lý do (ít nhất 5 ký tự).'; return; }
  const l = L.find(x => x.id === id);
  l.rr = r;
  _setSt(id, 'hidden');
  const last = NOTI[NOTI.length - 1];
  if (last && last.to === l.s) last.t += ' Lý do: ' + r;
  saveData();
  $('#dlg').close();
}

/* 2. Thống kê nhanh đầu trang quản trị */
const _dash = dash;
dash = function () {
  RP = RP.filter(x => L.some(l => l.id === x.l));   // bỏ báo cáo của tin không còn
  const c = s => L.filter(l => l.st === s).length;
  const box = (n, t) => `<div class="card pad" style="text-align:center"><div class="pr" style="font-size:24px">${n}</div><div class="mut">${t}</div></div>`;
  return `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-bottom:12px">${
    box(c('pending'), 'Chờ duyệt') + box(c('approved'), 'Đang bán') + box(c('sold'), 'Đã bán') + box(c('hidden'), 'Bị ẩn') + box(RP.filter(x => x.open).length, 'Báo cáo mở')}</div>` + _dash();
};

render();