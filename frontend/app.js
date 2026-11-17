const CUR=session();
const me=()=>CUR?CUR.id:null;
getUsers().forEach(u=>U[u.id]={n:u.name,h:'@'+u.email.split('@')[0]});
const S={view:'home',q:'',cat:-1,min:'',max:'',sort:'all',page:1,fav:new Set(),g:0,ot:'buy',og:'all'};
const FK='cdcsv_fav_'+(me()||'guest');
try{S.fav=new Set(JSON.parse(localStorage.getItem(FK)||'[]'))}catch(e){}
function save(){if(!saveData())toast('Bộ nhớ trình duyệt đầy, dữ liệu mới chưa được lưu.');try{if(CUR)localStorage.setItem(FK,JSON.stringify([...S.fav]))}catch(e){}}
function needLogin(){openDlg(`${dh('Cần đăng nhập')}<div class="db"><p style="margin:0">Hãy đăng nhập hoặc tạo tài khoản để tiếp tục.</p><div class="row"><a class="btn" style="flex:1;text-align:center" href="login.html#login">Đăng nhập</a><a class="btn o" style="flex:1;text-align:center" href="login.html#register">Đăng ký</a></div></div>`)}
addEventListener('storage',e=>{if(e.key===KEY){const had=new Set(NOTI.map(x=>x.id));loadData();const fresh=NOTI.filter(x=>CUR&&x.to===me()&&!had.has(x.id));refresh();if(fresh.length)toast('🔔 '+fresh[fresh.length-1].t)}});
const TAGS=[['Laptop','laptop'],['Sách','sach'],['Điện Thoại','dien thoai'],['Áo Khoác','ao khoac'],['Bàn Ghế','ban']];
const DAILY=5;

function toast(m){const t=$('#toast');t.textContent=m;t.style.display='block';clearTimeout(toast.h);toast.h=setTimeout(()=>t.style.display='none',3200)}
function rep(u){const r=R.filter(x=>x.to===u);return r.length?{avg:(r.reduce((a,b)=>a+b.star,0)/r.length).toFixed(1),n:r.length}:null}
function repTxt(u){const r=rep(u);return r?`★ ${r.avg} (${r.n} đánh giá)`:'Chưa có đánh giá'}
function tile(l){return `<div class="tile" style="--h:${l.id*47%360}">${l.im?`<img src="${l.im[0]}" alt="">`:`<span>${l.e}</span>`}`}
function card(l){return `<div class="li" tabindex="0" role="button" onclick="openDetail(${l.id})" onkeydown="if(event.key==='Enter')openDetail(${l.id})">
${tile(l)}${l.st==='sold'?'<b class="sold">Đã bán</b>':''}<button class="hrt ${S.fav.has(l.id)?'on':''}" aria-label="Lưu tin" onclick="fav(${l.id},event)">${S.fav.has(l.id)?'♥':'♡'}</button><span class="tm">${ago(l.a)}</span><span class="cn">🖼 ${l.n}</span></div>
<div class="inf"><b>${esc(l.t)}</b><div class="pr">${vnd(l.p)}</div><div class="mut">${CONDS[l.k]}</div></div></div>`.replace('<div class="li"','<div class="li"')}
function listing(){let a=L.filter(l=>l.st==='approved'||l.st==='sold');
 if(S.view==='saved')a=a.filter(l=>S.fav.has(l.id));
 const q=nz(S.q);if(q)a=a.filter(l=>nz(l.t+' '+l.ds).includes(q));
 if(S.cat>=0)a=a.filter(l=>l.c===S.cat);
 if(S.min!=='')a=a.filter(l=>l.p>=+S.min);
 if(S.max!=='')a=a.filter(l=>l.p<=+S.max);
 const o={all:(x,y)=>x.id-y.id,new:(x,y)=>x.a-y.a||y.id-x.id,high:(x,y)=>y.p-x.p,low:(x,y)=>x.p-y.p};
 return a.sort(o[S.sort])}

function renderRes(){const box=$('#res');
 if(!CUR&&(S.view==='mine'||S.view==='saved'||S.view==='orders'))return box.innerHTML='<div class="card empty"><p>Hãy đăng nhập để xem mục này.</p><a class="btn" href="login.html#login">Đăng nhập</a></div>';
 if(S.view==='mine')return box.innerHTML=mineHtml();
 if(S.view==='orders')return box.innerHTML=ordersHtml();
 const a=listing(),pages=Math.max(1,Math.ceil(a.length/10));S.page=Math.min(S.page,pages);
 const s=a.slice((S.page-1)*10,S.page*10);
 const T=[['all','🗂️','Tất cả'],['new','☆','Mới nhất'],['high','$','Giá cao nhất'],['low','$','Giá thấp nhất']];
 let h=S.view==='saved'?`<div class="card hh">Tin đã lưu (${a.length})</div>`:`<div class="card tabs">${T.map(t=>`<button class="tab ${S.sort===t[0]?'on':''}" onclick="setSort('${t[0]}')">${t[1]} ${t[2]}</button>`).join('')}</div>`;
 h+=s.length?`<div class="grid">${s.map(card).join('')}</div>`:`<div class="card empty">${S.view==='saved'?'Bạn chưa lưu tin nào. Nhấn ♡ trên một tin để lưu.':'Không có sản phẩm phù hợp. Thử bỏ bớt bộ lọc hoặc đổi từ khóa.'}</div>`;
 if(pages>1){h+=`<div class="pg"><button ${S.page<2?'disabled':''} onclick="pg(${S.page-1})" aria-label="Trang trước">‹</button>`;
  for(let i=1;i<=pages;i++)h+=`<button class="${i===S.page?'on':''}" onclick="pg(${i})">${i}</button>`;
  h+=`<button ${S.page>=pages?'disabled':''} onclick="pg(${S.page+1})" aria-label="Trang sau">›</button></div>`}
 box.innerHTML=h}
function pg(i){S.page=i;renderRes();window.scrollTo({top:$('#res').offsetTop-80})}
function setSort(v){S.sort=v;S.page=1;$('#fs').value=v;renderRes()}
function search(){S.q=$('#q').value.trim();S.cat=+$('#fc').value;S.min=$('#fmin').value;S.max=$('#fmax').value;S.sort=$('#fs').value;S.page=1;if(S.view!=='home')go('home');else{renderRes();side()}}
async function fav(id,e){
 if(e)e.stopPropagation();
 if(!CUR)return needLogin();
 const was=S.fav.has(id);
 try {
  await api("/listings/"+id+"/favorite",{method:was?"DELETE":"PUT"});
  if(was)S.fav.delete(id);else S.fav.add(id);
  renderRes();side();
 } catch(err){toast(err.message);}
}
function row(l,right,sub){return `<div class="ls"><div class="gr" onclick="openDetail(${l.id})">${''}<b>${esc(l.t)}</b><span class="mut">${vnd(l.p)} · ${esc(nm(l.s))} · ${ago(l.a)}${sub||''}</span></div>${right}</div>`.replace('<div class="gr"',`<div class="gr"`)}
const stB=l=>({pending:'<span class="badge w">Chờ duyệt</span>',approved:'<span class="badge">Đang bán</span>',sold:'<span class="badge">Đã bán</span>',hidden:'<span class="badge x">Bị ẩn</span>'}[l.st]);
function mineHtml(){
 const a=L.filter(l=>l.s===me()),b=O.filter(o=>o.f===me());
 return `<div class="card"><div class="hh">Tin của tôi (${a.length}) · hôm nay ${todayCount()}/${DAILY}</div>${a.length?a.map(l=>{const n=O.filter(o=>o.l===l.id&&o.st==='pending').length;return row(l,`<div class="acts">${stB(l)}${n?`<span class="badge w">${n} đề nghị mới</span>`:''}</div>`)}).join(''):'<div class="empty">Bạn chưa đăng tin nào.</div>'}</div>
 <div class="card"><div class="hh">Đề nghị trả giá của tôi (${b.length})</div>${b.length?b.map(o=>{const l=L.find(x=>x.id===o.l);return row(l,`<div class="acts"><span class="badge ${o.st==='rejected'?'x':o.st==='pending'?'w':''}">${{pending:'Chờ người bán phản hồi',accepted:'Đã được chấp nhận',rejected:'Bị từ chối'}[o.st]}</span><b>${vnd(o.p)}</b></div>`)}).join(''):'<div class="empty">Bạn chưa gửi đề nghị trả giá nào.</div>'}</div>
 <div class="card pad" style="display:flex;justify-content:space-between;align-items:center;gap:12px"><span>Đơn bạn đã mua và đã bán nằm ở mục <b>Đơn hàng</b>.</span><button class="btn sm" onclick="openOrders('buy')">Xem đơn hàng</button></div>`;
}
function todayCount(){return L.filter(l=>l.s===me()&&l.a===0).length}
function openDlg(h){const d=$('#dlg');d.innerHTML=h;if(!d.open)d.showModal()}
$('#dlg').addEventListener('click',e=>{if(e.target.id==='dlg')e.target.close()});
const dh=t=>`<div class="dh">${t}<button aria-label="Đóng" onclick="$('#dlg').close()">×</button></div>`;
function galHtml(l){const n=l.im?l.im.length:l.n;S.g=(S.g+n)%n;return `<div class="gal" style="--h:${l.id*47%360}">${l.im?`<img src="${l.im[S.g]}" alt="">`:`<span>${l.e}</span>`}${n>1?`<button class="pv" aria-label="Ảnh trước" onclick="gal(${l.id},-1)">‹</button><button class="nx" aria-label="Ảnh sau" onclick="gal(${l.id},1)">›</button>`:''}<b class="cnt">${S.g+1}/${n}</b></div>`}
function gal(id,d){S.g+=d;$('#galw').innerHTML=galHtml(L.find(x=>x.id===id))}
function openDetail(id){const l=L.find(x=>x.id===id);S.g=0;const mine=!!CUR&&l.s===me(),m=me(),offs=O.filter(o=>o.l===id),ods=ORD.filter(o=>o.l===id&&o.st!=='cancelled');
 let act='';
 if(!CUR)act=`<div class="box"><b>Đăng nhập để mua sản phẩm hoặc lưu tin</b><a class="btn" href="login.html#login">Đăng nhập</a></div>`;
 else if(mine)act=`<div class="box"><b>Đề nghị trả giá (${offs.length})</b>${offs.length?offs.map(o=>`<div class="sel" style="align-items:flex-start"><div style="flex:1"><b>${esc(nm(o.f))} · ${vnd(o.p)}</b><div class="mut" style="white-space:pre-line;margin-top:4px">${esc(o.m||'Không có lời nhắn')}</div></div>${o.st==='pending'&&l.st==='approved'?`<button class="btn sm" onclick="accept(${o.id})">Chấp nhận</button><button class="btn sm o" onclick="rejectO(${o.id})">Từ chối</button>`:`<span class="badge ${o.st==='rejected'?'x':''}">${{pending:'Chờ',accepted:'Đã chấp nhận',rejected:'Đã từ chối'}[o.st]}</span>`}</div>`).join(''):'<span class="mut">Chưa có ai gửi đề nghị trả giá.</span>'}</div>${ods.length?`<div class="box"><b>Đơn hàng của tin này</b>${ods.map(o=>`<div class="sel"><div style="flex:1"><b>#${o.code} · ${esc(o.name)}</b><div class="mut">${vnd(o.p)} · ${OST[o.st][0]}</div></div></div>`).join('')}<button class="btn" onclick="openOrders('sell')">Quản lý đơn bán</button></div>`:''}`;
 else if(l.st==='approved'){const mo=offs.find(o=>o.f===m);
  act=`<div class="box"><b>Mua sản phẩm / Gửi đề nghị</b>${mo?`<div><span class="badge w">Bạn đã gửi đề nghị giá ${vnd(mo.p)}. Chờ người bán phản hồi.</span><div class="mut" style="white-space:pre-line;margin-top:6px">${esc(mo.m)}</div></div>`:`
  <div class="row" style="margin-bottom:8px">
    <button class="btn" style="flex:1" onclick="openBuyForm(${id})">⚡ Mua ngay (${vnd(l.p)})</button>
  </div>
  <div class="two"><label class="f" id="fp">Hoặc giá đề nghị (đ)<input id="op" type="number" min="1000" value="${l.p}"><span class="err" id="ep"></span></label><label class="f">Lời nhắn<input id="om" maxlength="120" placeholder="Hẹn gặp ở cổng trường..."></label></div>
  <button class="btn o" onclick="offer(${id})">Gửi đề nghị trả giá</button>`}
  <div class="row"><button class="btn o sm" onclick="fav(${id},event);openDetail(${id})">${S.fav.has(id)?'♥ Đã lưu':'♡ Lưu tin'}</button><button class="btn o sm" onclick="repForm(${id})">🚩 Báo cáo tin</button></div></div>`}
 else{const my=ods.find(o=>o.b===m);
  act=my?`<div class="box" style="border-color:var(--g)"><b>🎉 Cảm ơn bạn đã đặt hàng!</b><div>Mã đơn <b>#${my.code}</b> · <span class="badge ${OST[my.st][1]}">${OST[my.st][0]}</span></div>${my.st==='done'?`<div class="mut">Bạn đã nhận hàng lúc ${fdt(my.ts.done)}.</div>`:`<div class="mut">🚚 Dự kiến giao: <b>${fd(my.eta)}</b></div>`}<div class="row"><button class="btn" style="flex:1" onclick="openOrders('buy')">Xem đơn hàng</button>${my.st==='done'&&!my.rv?`<button class="btn o" style="flex:1" onclick="reviewForm(${my.id})">★ Đánh giá người bán</button>`:''}</div></div>`:'<span class="mut">Tin này đã bán.</span>'}
 openDlg(`${dh(esc(l.t))}<div class="db"><div id="galw">${galHtml(l)}</div>
 <div><div class="pr" style="font-size:22px">${vnd(l.p)}</div><div class="mut">${stB(l)} ${CATS[l.c][0]} · ${CONDS[l.k]} · ${ago(l.a)}</div></div>
 <p style="margin:0">${esc(l.ds)}</p>
 <div class="sel"><div class="av">${nm(l.s)[0]}</div><div><b>${esc(nm(l.s))}</b><div class="mut">${repTxt(l.s)}</div></div></div>${act}</div>`)}

// ===== ĐƠN HÀNG =====
const OST={pending:['Chờ xác nhận','w'],confirmed:['Đã xác nhận',''],shipping:['Đang giao',''],done:['Hoàn tất',''],cancelled:['Đã hủy','x']};
const OGRP={all:'Tất cả',pending:'Chờ xác nhận',active:'Đang xử lý & giao',done:'Hoàn tất',cancelled:'Đã hủy'};
const inGrp=(o,g)=>g==='all'||(g==='active'?(o.st==='confirmed'||o.st==='shipping'):o.st===g);
const fdt=t=>new Date(t).toLocaleString('vi-VN',{hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit',year:'numeric'});
const fd=t=>new Date(t).toLocaleDateString('vi-VN',{weekday:'long',day:'2-digit',month:'2-digit',year:'numeric'});
const etaFor=(pay,t)=>t+(pay.includes('trực tiếp')?1:pay.includes('COD')?3:2)*864e5;
const newCode=()=>'DH'+Date.now().toString(36).toUpperCase().slice(-6);
const ordBadge=()=>{const m=me();return ORD.filter(o=>(o.b===m&&o.st==='shipping')||(o.s===m&&(o.st==='pending'||o.st==='confirmed'))).length};
function openOrders(t){S.ot=t;S.og='all';$('#dlg').close();go('orders')}
function setOt(t){S.ot=t;S.og='all';renderRes()}
function setOg(g){S.og=g;renderRes()}
function ordersHtml(){const m=me(),buy=ORD.filter(o=>o.b===m),sell=ORD.filter(o=>o.s===m);
 const list=(S.ot==='sell'?sell:buy).filter(o=>inGrp(o,S.og)).sort((a,b)=>b.ts.pending-a.ts.pending);
 return `<div class="card tabs" style="grid-template-columns:1fr 1fr"><button class="tab ${S.ot!=='sell'?'on':''}" onclick="setOt('buy')">🛒 Đơn mua (${buy.length})</button><button class="tab ${S.ot==='sell'?'on':''}" onclick="setOt('sell')">🏷️ Đơn bán (${sell.length})</button></div>
 <div class="ofl">${Object.entries(OGRP).map(([k,v])=>`<button class="chip ${S.og===k?'on':''}" onclick="setOg('${k}')">${v}</button>`).join('')}</div>
 ${list.length?list.map(orderCard).join(''):`<div class="card empty">${S.og==='all'?(S.ot==='sell'?'Bạn chưa có đơn bán nào. Khi có người đặt mua tin của bạn, đơn sẽ hiện ở đây.':'Bạn chưa có đơn mua nào. Hãy chọn một sản phẩm và bấm Mua ngay.'):'Không có đơn nào ở trạng thái này.'}</div>`}`}
function orderCard(o){const l=L.find(x=>x.id===o.l)||{id:0,t:'(Tin không còn tồn tại)',e:'📦'},buyer=o.b===me(),oth=buyer?o.s:o.b,[sl,sc]=OST[o.st];
 const idx=['pending','confirmed','shipping','done'].indexOf(o.st),steps=[['pending','Đã đặt hàng'],['confirmed','Đã xác nhận'],['shipping','Đang giao'],['done','Đã nhận hàng']];
 const stp=o.st==='cancelled'?`<div class="ocx">❌ Đơn đã hủy lúc ${fdt(o.ts.cancelled)} ${o.by==='seller'?'bởi người bán':'bởi người mua'}.</div>`:
  `<ol class="stp">${steps.map((s,i)=>{const ok=i<idx||o.st==='done';return `<li class="${ok?'ok':i===idx?'cur':''}"><i>${ok?'✓':i+1}</i><b>${s[1]}</b><small>${o.ts[s[0]]?fdt(o.ts[s[0]]):''}</small></li>`}).join('')}</ol>
  <div class="oe">${o.st==='done'?`✅ Đã nhận hàng lúc <b>${fdt(o.ts.done)}</b>`:`🚚 Dự kiến giao: <b>${fd(o.eta)}</b>`}</div>`;
 const info=[`👤 Người nhận: <b>${esc(o.name)}</b> · ${esc(o.phone||'chưa có SĐT')}`,`📍 ${esc(o.addr)}`,`💳 ${esc(o.pay)}`,o.note?`📝 ${esc(o.note)}`:''].filter(Boolean).map(x=>`<span class="mut">${x}</span>`).join('');
 let a='';
 if(buyer){if(o.st==='pending')a+=`<button class="btn sm r" onclick="askCancel(${o.id})">Hủy đơn</button>`;
  if(o.st==='shipping')a+=`<button class="btn sm" onclick="receiveOrder(${o.id})">Đã nhận hàng</button>`;
  if(o.st==='done')a+=o.rv?'<span class="badge">★ Đã đánh giá</span>':`<button class="btn sm" onclick="reviewForm(${o.id})">★ Đánh giá người bán</button>`}
 else{if(o.st==='pending')a+=`<button class="btn sm" onclick="sellerStep(${o.id},'confirmed')">Xác nhận đơn</button><button class="btn sm r" onclick="askRefuse(${o.id})">Từ chối</button>`;
  if(o.st==='confirmed')a+=`<button class="btn sm" onclick="sellerStep(${o.id},'shipping')">Bắt đầu giao hàng</button>`;
  if(o.st==='shipping')a+='<span class="mut">Chờ người mua xác nhận đã nhận hàng</span>'}
 return `<div class="ocard"><div class="oh"><span>Mã đơn <b>#${o.code}</b> · ${fdt(o.ts.pending)}</span><span class="badge ${sc}">${sl}</span></div>
 <div class="ob"><div class="tile" style="--h:${l.id*47%360}">${l.im?`<img src="${l.im[0]}" alt="">`:`<span>${l.e}</span>`}</div><div class="oi"><b>${esc(l.t)}</b><span class="pr">${vnd(o.p)}</span><span class="mut">${buyer?'Người bán':'Người mua'}: ${esc(U[oth]?U[oth].n:'Người dùng')}</span>${info}</div></div>
 ${stp}<div class="oa">${l.id?`<button class="btn sm o" onclick="openDetail(${l.id})">Xem sản phẩm</button>`:''}${a}</div></div>`}
function askDlg(title,msg,yes,fn){window._ask=fn;openDlg(`${dh(title)}<div class="db"><p style="margin:0">${msg}</p><div class="row"><button class="btn o" style="flex:1" onclick="$('#dlg').close()">Không</button><button class="btn r" style="flex:1" onclick="$('#dlg').close();_ask()">${yes}</button></div></div>`)}
function askCancel(id){askDlg('Hủy đơn hàng?','Bạn chắc chắn muốn hủy đơn này? Sản phẩm sẽ được mở bán lại.','Hủy đơn',()=>setOrd(id,'cancelled','Đã hủy đơn hàng.','b'))}
function askRefuse(id){askDlg('Từ chối đơn hàng?','Người mua sẽ được báo là đơn đã bị hủy và sản phẩm được mở bán lại.','Từ chối',()=>setOrd(id,'cancelled','Đã từ chối đơn hàng.','s'))}
function sellerStep(id,st){setOrd(id,st,st==='confirmed'?'Đã xác nhận đơn. Hãy chuẩn bị hàng.':'Đã chuyển sang đang giao hàng.','s')}
function receiveOrder(id){setOrd(id,'done','Cảm ơn bạn! Đơn hàng đã hoàn tất.','b');reviewForm(id)}
function setOrd(id,st,msg,who){const o=ORD.find(x=>x.id===id),now=Date.now();
 if(!CUR||!o||(who==='b'?o.b:o.s)!==me())return toast('Bạn không có quyền thao tác đơn này (403).');
 const ok={cancelled:who==='b'?o.st==='pending':o.st==='pending',confirmed:o.st==='pending',shipping:o.st==='confirmed',done:o.st==='shipping'}[st];
 if(!ok)return toast('Đơn hàng không còn ở trạng thái phù hợp để thao tác.');
 o.st=st;o.ts[st]=now;if(st==='cancelled')o.by=who==='b'?'buyer':'seller';if(st==='confirmed')o.eta=etaFor(o.pay,now);
 if(st==='cancelled'){const l=L.find(x=>x.id===o.l);if(l&&l.st==='sold'&&!ORD.some(x=>x.l===o.l&&x.id!==o.id&&x.st!=='cancelled'))l.st='approved'}
 {const ll=L.find(x=>x.id===o.l),tt=ll?ll.t:'sản phẩm';
  if(st==='confirmed')notify(o.b,`Đơn #${o.code} (${tt}) đã được xác nhận. Dự kiến giao ${fd(o.eta)}`,'orders:buy','✅');
  if(st==='shipping')notify(o.b,`Đơn #${o.code} (${tt}) đang được giao đến bạn`,'orders:buy','🚚');
  if(st==='done')notify(o.s,`${nm(o.b)} đã nhận hàng. Đơn #${o.code} hoàn tất`,'orders:sell','📦');
  if(st==='cancelled'){if(who==='b')notify(o.s,`${nm(o.b)} đã hủy đơn #${o.code} (${tt})`,'orders:sell','❌');else notify(o.b,`Người bán đã từ chối đơn #${o.code} (${tt})`,'orders:buy','❌')}}
 toast(msg);refresh(true)}
function reviewForm(oid){openDlg(`${dh('Đánh giá người bán')}<div class="db"><div class="two"><label class="f">Số sao<select id="ors"><option value="5">5 ★ Rất tốt</option><option value="4">4 ★ Tốt</option><option value="3">3 ★ Bình thường</option><option value="2">2 ★ Chưa tốt</option><option value="1">1 ★ Tệ</option></select></label><label class="f">Nhận xét<input id="orx" maxlength="200" placeholder="Giao hàng đúng hẹn, đồ đẹp..."></label></div><button class="btn" onclick="submitReview(${oid})">Gửi đánh giá</button></div>`)}
function submitReview(oid){const o=ORD.find(x=>x.id===oid);if(!o||o.b!==me()||o.st!=='done'||o.rv)return toast('Không thể đánh giá đơn này.');
 R.push({l:o.l,to:o.s,f:me(),star:+$('#ors').value,x:$('#orx').value.trim()||'Không có nhận xét'});o.rv=true;notify(o.s,`${nm(me())} đã đánh giá bạn ${R[R.length-1].star} sao cho đơn #${o.code}`,'orders:sell','⭐');$('#dlg').close();toast('Cảm ơn bạn đã đánh giá người bán.');refresh(true)}

// FORM ĐIỀN THÔNG TIN ĐẶT MUA & GIAO HÀNG
function openBuyForm(id){
 const l=L.find(x=>x.id===id),m=me();
 if(ORD.some(o=>o.l===id&&o.b===m&&o.st!=='cancelled'))return toast('Bạn đã đặt mua sản phẩm này rồi.');
 openDlg(`${dh('Thông tin đặt mua & nhận hàng')}<div class="db">
  <div class="sel" style="background:var(--bg);padding:10px;border-radius:8px">
   <div style="flex:1"><b>${esc(l.t)}</b><div class="pr">${vnd(l.p)}</div></div>
   <span class="mut">Người bán: ${esc(nm(l.s))}</span>
  </div>
  <div class="two">
   <label class="f" id="bf_name">Tên người nhận *<input id="bname" maxlength="60" value="${esc(nm(m))}"><span class="err"></span></label>
   <label class="f" id="bf_phone">Số điện thoại *<input id="bphone" type="tel" maxlength="15" placeholder="09xxxxxxxx" value="${esc(CUR.phone||'')}"><span class="err"></span></label>
  </div>
  <label class="f" id="bf_addr">Địa chỉ giao hàng / Điểm hẹn nhận đồ *<input id="baddr" maxlength="200" placeholder="VD: Cổng chính trường, KTX nhà A3, hoặc số nhà..."><span class="err"></span></label>
  <label class="f">Hình thức giao & thanh toán
   <select id="bpay">
    <option value="Gặp trực tiếp tại trường / Kiểm tra hàng rồi trả tiền">Gặp trực tiếp tại trường / Kiểm tra hàng rồi trả tiền</option>
    <option value="Ship COD (Nhận hàng tại nhà & thanh toán)">Ship COD (Nhận hàng tại nhà & thanh toán)</option>
    <option value="Chuyển khoản ngân hàng">Chuyển khoản ngân hàng</option>
   </select>
  </label>
  <label class="f">Ghi chú cho người bán (tuỳ chọn)<input id="bnote" maxlength="120" placeholder="VD: Giao giúp mình sau 5h chiều nhé..."></label>
  <div class="row">
   <button class="btn o" style="flex:1" onclick="openDetail(${id})">← Quay lại</button>
   <button class="btn" style="flex:2" onclick="submitBuy(${id})">Xác nhận đặt mua (${vnd(l.p)})</button>
  </div>
 </div>`);
}

function submitBuy(id){
 const bad=(fid,msg)=>{const f=$('#'+fid);f.classList.add('bad');f.querySelector('.err').textContent=msg;return 1};
 ['bf_name','bf_phone','bf_addr'].forEach(i=>{$('#'+i).classList.remove('bad');$('#'+i).querySelector('.err').textContent=''});
 const name=$('#bname').value.trim(),phone=$('#bphone').value.trim(),addr=$('#baddr').value.trim(),pay=$('#bpay').value,note=$('#bnote').value.trim();
 let e=0;
 if(name.length<2)e+=bad('bf_name','Vui lòng nhập tên người nhận.');
 if(!/^0\d{8,10}$/.test(phone.replace(/\s+/g,'')))e+=bad('bf_phone','Số điện thoại chưa đúng định dạng (10-11 số).');
 if(addr.length<5)e+=bad('bf_addr','Vui lòng nhập rõ địa chỉ hoặc điểm hẹn giao hàng.');
 if(e)return;
 const l=L.find(x=>x.id===id),m=me();
 if(l.st!=='approved'||l.s===m)return toast('Tin này không còn có thể đặt mua.');
 const now=Date.now(),o={id:ORD.length+1,code:newCode(),l:id,b:m,s:l.s,p:l.p,name,phone,addr,pay,note,st:'pending',ts:{pending:now},eta:etaFor(pay,now)};
 ORD.push(o);l.st='sold';
 notify(l.s,`${nm(m)} vừa đặt mua "${l.t}" (${vnd(l.p)}). Đơn #${o.code} đang chờ bạn xác nhận`,'orders:sell','🛒');
 notify(m,`Bạn đã đặt hàng #${o.code} (${l.t}). Chờ người bán xác nhận`,'orders:buy','🧾');
 openDlg(`${dh('Đặt hàng thành công')}<div class="db" style="text-align:center"><div style="font-size:56px">🎉</div><h3 style="margin:0">Cảm ơn bạn đã đặt hàng!</h3>
  <div class="mut">Mã đơn <b>#${o.code}</b> · ${esc(l.t)} · ${vnd(l.p)}</div>
  <div class="box" style="text-align:left"><div>🚚 Dự kiến giao: <b>${fd(o.eta)}</b></div><div class="mut">Người bán sẽ xác nhận và liên hệ qua số ${esc(phone)}. Bạn theo dõi tiến trình ở mục <b>Đơn hàng</b>.</div></div>
  <div class="row"><button class="btn o" style="flex:1" onclick="$('#dlg').close()">Tiếp tục mua sắm</button><button class="btn" style="flex:1" onclick="openOrders('buy')">Xem đơn hàng</button></div></div>`);
 refresh(true);
}

async function offer(id){
 const p=+$('#op').value,f=$('#fp');
 if(!Number.isInteger(p)||p<1000){f.classList.add('bad');$('#ep').textContent='Giá phải là số nguyên từ 1.000đ trở lên.';return}
 try {
  const x=await api('/listings/'+id+'/offers',{method:'POST',body:JSON.stringify({amount:p,message:$('#om').value.trim()||null})});
  O=O.filter(o=>!(o.l===id&&o.f===me()));O.push(mapOffer(x));
  toast('Đã gửi đề nghị. Chờ người bán phản hồi.');openDetail(id);refresh(true);
 } catch(err){toast(err.message);}
}
async function accept(oid){
 const old=O.find(o=>o.id===oid);if(!old)return;
 try {
  const x=await api('/offers/'+oid+'/accept',{method:'POST'});
  await loadFromApi();toast('Đã chấp nhận đề nghị.');openDetail(old.l);refresh(true);
 } catch(err){toast(err.message);}
}
async function rejectO(oid){
 const old=O.find(o=>o.id===oid);if(!old)return;
 try {
  await api('/offers/'+oid+'/reject',{method:'POST'});
  await loadFromApi();toast('Đã từ chối đề nghị.');openDetail(old.l);refresh(true);
 } catch(err){toast(err.message);}
}
function review(id){const l=L.find(x=>x.id===id);R.push({l:id,to:l.s,f:me(),star:+$('#rs').value,x:$('#rx').value.trim()||'Không có nhận xét'});toast('Cảm ơn bạn đã đánh giá người bán.');openDetail(id)}
function repForm(id){openDlg(`${dh('Báo cáo tin vi phạm')}<div class="db"><label class="f">Lý do<select id="rr"><option>Lừa đảo hoặc nghi ngờ lừa đảo</option><option>Ảnh không đúng sản phẩm</option><option>Hàng cấm hoặc không phù hợp</option><option>Spam</option></select></label><button class="btn r" onclick="sendRep(${id})">Gửi báo cáo</button></div>`)}
async function sendRep(id){
 const reasons={ 'Lừa đảo hoặc nghi ngờ lừa đảo':'fraud','Ảnh không đúng sản phẩm':'inappropriate','Hàng cấm hoặc không phù hợp':'prohibited_item','Spam':'spam' };
 try {
  await api('/listings/'+id+'/reports',{method:'POST',body:JSON.stringify({reason_code:reasons[$('#rr').value]||'other'})});
  $('#dlg').close();toast('Đã gửi báo cáo. Kiểm duyệt viên sẽ xem xét.');
 } catch(err){toast(err.message);}
}
let pics=[];
function openPost(){if(!CUR)return needLogin();pics=[];
 openDlg(`${dh('Đăng tin bán')}<div class="db"><div class="mut">Hôm nay bạn đã đăng ${todayCount()}/${DAILY} tin. Tin cần kiểm duyệt viên duyệt trước khi hiển thị.</div>
 <label class="f" id="pt">Tiêu đề<input id="pti" maxlength="80" placeholder="Ví dụ: Giáo trình Vật lý đại cương"><span class="err"></span></label>
 <div class="two"><label class="f" id="pp">Giá (đ)<input id="ppr" type="number" min="1000"><span class="err"></span></label><label class="f" id="pc">Danh mục<select id="pca"><option value="">Chọn danh mục</option>${CATS.map((c,i)=>`<option value="${i}">${c[0]}</option>`).join('')}</select><span class="err"></span></label></div>
 <label class="f">Tình trạng<select id="pk">${CONDS.map((c,i)=>`<option value="${i}">${c}</option>`).join('')}</select></label>
 <label class="f">Mô tả<textarea id="pd" rows="3" maxlength="500"></textarea></label>
 <div class="f" id="pi">Ảnh (tối đa 5)<input type="file" accept="image/*" multiple onchange="pickImgs(this)"><div class="thumbs" id="th"></div><span class="err"></span></div>
 <button class="btn" onclick="submitPost()">Gửi duyệt</button></div>`)}
function pickImgs(inp){const fs=[...inp.files].slice(0,5);pics=[];$('#th').innerHTML='';fs.forEach(f=>{const r=new FileReader();r.onload=()=>{pics.push(r.result);$('#th').insertAdjacentHTML('beforeend',`<img src="${r.result}" alt="">`)};r.readAsDataURL(f)})}
function submitPost(){const bad=(id,m)=>{const f=$('#'+id);f.classList.add('bad');f.querySelector('.err').textContent=m;return 1};
 ['pt','pp','pc','pi'].forEach(i=>{$('#'+i).classList.remove('bad');$('#'+i).querySelector('.err').textContent=''});
 const t=$('#pti').value.trim(),p=+$('#ppr').value,c=$('#pca').value;let e=0;
 if(t.length<5)e+=bad('pt','Tiêu đề cần ít nhất 5 ký tự.');
 if(!Number.isInteger(p)||p<1000)e+=bad('pp','Giá phải là số nguyên từ 1.000đ trở lên.');
 if(c==='')e+=bad('pc','Hãy chọn danh mục.');
 if(!pics.length)e+=bad('pi','Cần ít nhất 1 ảnh.');
 if(e)return;
 if(todayCount()>=DAILY){$('#dlg').close();return toast(`Bạn đã đạt giới hạn ${DAILY} tin mỗi ngày (lỗi 429). Hãy quay lại vào ngày mai.`)}
 L.push({id:L.length+1,t,p,c:+c,k:+$('#pk').value,s:me(),a:0,n:pics.length,im:pics.slice(),st:'pending',e:CATS[+c][1],ds:$('#pd').value.trim()||'Không có mô tả.'});
 notify(me(),`Tin "${t}" đã được gửi, đang chờ kiểm duyệt`,'mine','📝');
 $('#dlg').close();toast('Đã gửi tin. Tin sẽ hiển thị sau khi kiểm duyệt viên duyệt.');go('mine')}
function side(){
 const u=CUR
  ?(U[me()]||(U[me()]={n:CUR.name||CUR.email||'Bạn',h:'@'+String(CUR.email||'').split('@')[0]}))
  :{n:'Khách',h:'Chưa đăng nhập'},
  ini=u.n[0];
 $('#pn').textContent=u.n;$('#ph').textContent=u.h;
 ['pav','cav'].forEach(i=>$('#'+i).textContent=CUR?ini:'?');
 $('#cmpt').textContent=CUR?`${u.n} ơi, bạn cần bán gì hôm nay?`:'Đăng nhập để bắt đầu bán hàng';
 $('#who').innerHTML=CUR?bellHtml()+userMenu(u,ini):`<a class="btn o sm" href="login.html#login">Đăng nhập</a><a class="btn sm" href="login.html#register">Đăng ký</a>`;
 $('#onl').innerHTML=CUR?`<div class="av on">${esc(ini)}</div>${esc(u.n)}`:'<span class="mut">Đăng nhập để hiện ở đây</span>';
 const N=[['home','🏪','Mua sắm'],['home','📦','Tìm sản phẩm','find'],['saved','♡','Đã lưu']];
 if(CUR){N.push(['mine','👤','Tin của tôi']);const c=ordBadge();N.push(['orders','🧾','Đơn hàng'+(c?` <span class="nbd">${c}</span>`:'')])}
 $('#nv').innerHTML=N.map(n=>`<button class="${n[3]?'':S.view===n[0]?'on':''}" onclick="${n[3]?`go('home');$('#q').focus()`:`go('${n[0]}')`}"><span class="ic">${n[1]}</span>${n[2]}</button>`).join('');
 const vis=L.filter(l=>l.st==='approved'||l.st==='sold');
 $('#cats').innerHTML=CATS.map((c,i)=>`<button class="cat ${S.cat===i?'on':''}" onclick="pickCat(${i})"><span>${c[1]}</span><span>${c[0]}</span><em>${vis.filter(l=>l.c===i).length}</em></button>`).join('');
 $('#s1').textContent='+'+vis.filter(l=>l.a===0).length;
 $('#trend').innerHTML=[['#Macbook','2.1k','macbook'],['#Bàn phím cơ','1.8k','ban phim'],['#Điện thoại','1.5k','dien thoai'],['#Laptop','1.2k','laptop'],['#Tai nghe','980','tai nghe']].map((t,i)=>`<button class="tr" onclick="tag('${t[2]}')"><i style="color:${['#d98a0b','#e0883e','#c9a400','inherit','inherit'][i]}">${i+1}</i><span>${t[0]}</span><span class="mut" style="flex:none">${t[1]}</span></button>`).join('');
 $('#hot').innerHTML=CATS.slice(0,4).map((c,i)=>`<button class="chip" onclick="pickCat(${i})">${c[0]}</button>`).join('')
}
function pickCat(i){S.cat=S.cat===i?-1:i;$('#fc').value=S.cat;S.page=1;if(S.view!=='home')go('home');else{renderRes();side()}}
function tag(k){$('#q').value=k;search()}
function go(v){if(location.hash!=='#'+v)location.hash=v;else route()}
function route(){const v=location.hash.slice(1);S.view=['home','saved','mine','orders'].includes(v)?v:'home';S.page=1;refresh()}
function refresh(keep){save();const v=S.view;$('#cmp').style.display=$('#sc').style.display=v==='home'?'':'none';side();renderRes()}
$('#chips').innerHTML=TAGS.map(t=>`<button class="chip" onclick="tag('${t[1]}')">#${t[0]}</button>`).join('');
$('#fc').innerHTML='<option value="-1">Tất cả danh mục</option>'+CATS.map((c,i)=>`<option value="${i}">${c[0]}</option>`).join('');
addEventListener('hashchange',route);
loadFromApi().then(route).catch(e=>{
  console.error(e);
  $('#res').innerHTML='<div class="card empty">Không tải được dữ liệu từ máy chủ. Vui lòng kiểm tra kết nối Backend rồi tải lại trang.</div>';
});

// ===== MENU NGƯỜI DÙNG (góc phải) =====
function ico(n){return {
 user:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>',
 heart:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-8-5.2-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 5.8-8 11-8 11z"/></svg>',
 box:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/></svg>',
 receipt:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/></svg>',
 lock:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>'}[n]}
function userMenu(u,ini){return `<div class="um"><button class="ump" id="umb" aria-haspopup="true" aria-expanded="false" onclick="toggleUM()"><span class="av on">${esc(ini)}</span><b class="wn">${esc(u.n)}</b><svg class="chev" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></button>
 <div class="umm" id="umm" role="menu" hidden>
  <button role="menuitem" onclick="umGo('profile')">${ico('user')}Thông tin tài khoản</button>
  <button role="menuitem" onclick="umGo('saved')">${ico('heart')}Tin đăng đã lưu</button>
  <button role="menuitem" onclick="umGo('mine')">${ico('box')}Quản lý bài đăng</button>
  <button role="menuitem" onclick="umGo('orders')">${ico('receipt')}Đơn hàng</button>
  <hr><button role="menuitem" onclick="logout();location.href='login.html'">${ico('lock')}Đăng xuất</button>
 </div></div>`}
function toggleUM(){const m=$('#umm'),open=m.hidden;m.hidden=!open;$('#umb').setAttribute('aria-expanded',open)}
function closeUM(){const m=$('#umm');if(m){m.hidden=true;$('#umb').setAttribute('aria-expanded','false')}}
function umGo(k){closeUM();if(k==='profile')return openProfile();if(k==='orders'){S.ot='buy';S.og='all'}go(k)}
document.addEventListener('click',e=>{if(!e.target.closest('.um'))closeUM()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeUM()});
function openProfile(){const m=me();
 openDlg(`${dh('Thông tin tài khoản')}<div class="db"><div class="sel"><div class="av lg" style="text-transform:uppercase">${esc(CUR.name[0])}</div><div><b>${esc(CUR.name)}</b><div class="mut">${repTxt(m)}</div></div></div>
 <label class="f" id="pf_name">Họ và tên<input id="pfn" maxlength="100" value="${esc(CUR.name)}"><span class="err"></span></label>
 <div class="two"><label class="f">Email<input value="${esc(CUR.email)}" disabled></label><label class="f">Mã sinh viên<input value="${esc(CUR.mssv||'Chưa cập nhật')}" disabled></label></div>
 <div class="mut">Tin đã đăng: <b>${L.filter(l=>l.s===m).length}</b> · Đơn mua: <b>${ORD.filter(o=>o.b===m).length}</b> · Đơn bán: <b>${ORD.filter(o=>o.s===m).length}</b></div>
 <button class="btn" onclick="saveProfile()">Lưu thay đổi</button></div>`)}
async function saveProfile(){
 const name=$('#pfn').value.trim();
 if(name.length<2){$('#pf_name').classList.add('bad');$('#pf_name .err').textContent='Nhập họ và tên (ít nhất 2 ký tự).';return;}
 try {
  const updated=await api('/users/me',{method:'PATCH',body:JSON.stringify({full_name:name})});
  CUR.name=updated.full_name;
  if(U[CUR.id])U[CUR.id].n=CUR.name;
  sessionStorage.setItem(AUTH_BUSER_KEY,JSON.stringify(CUR));
  $('#dlg').close();toast('Đã cập nhật thông tin tài khoản.');refresh(true);
 } catch(err){toast(err.message);}
}
// ===== THÔNG BÁO (chuông) =====
function nm(id){return U[id]?U[id].n:(CUR&&id===me()?(CUR.name||CUR.email||'Bạn'):'Người dùng')}
function timeAgo(t){const m=Math.floor((Date.now()-t)/6e4);return m<1?'Vừa xong':m<60?m+' phút trước':m<1440?Math.floor(m/60)+' giờ trước':Math.floor(m/1440)+' ngày trước'}
function bellHtml(){const mine=NOTI.filter(x=>x.to===me()).sort((a,b)=>b.ts-a.ts).slice(0,20),n=mine.filter(x=>!x.read).length;
 return `<div class="bl"><button class="blb" id="blb" aria-label="Thông báo${n?' ('+n+' chưa đọc)':''}" aria-haspopup="true" aria-expanded="false" onclick="toggleBell()"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/></svg>${n?`<i class="bdg">${n>9?'9+':n}</i>`:''}</button>
 <div class="blm" id="blm" hidden><div class="blh"><b>Thông báo</b><button onclick="readAll()">Đánh dấu đã đọc</button></div><div class="bll">${mine.length?mine.map(x=>`<button class="bli ${x.read?'':'un'}" onclick="openNoti(${x.id})"><span class="bie">${x.ic}</span><span><b>${esc(x.t)}</b><small>${timeAgo(x.ts)}</small></span></button>`).join(''):'<div class="bln">Chưa có thông báo nào.</div>'}</div></div></div>`}
function toggleBell(){const m=$('#blm'),open=m.hidden;closeUM();m.hidden=!open;$('#blb').setAttribute('aria-expanded',open)}
function closeBell(){const m=$('#blm');if(m){m.hidden=true;$('#blb').setAttribute('aria-expanded','false')}}
function readAll(){NOTI.forEach(x=>{if(x.to===me())x.read=true});save();side()}
function openNoti(id){const n=NOTI.find(x=>x.id===id);if(!n||n.to!==me())return;n.read=true;save();closeBell();
 const [v,t]=n.link.split(':');if(v==='orders'){S.ot=t||'buy';S.og='all'}go(['home','saved','mine','orders'].includes(v)?v:'home');side()}
document.addEventListener('click',e=>{if(!e.target.closest('.bl'))closeBell()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeBell()});
addEventListener('storage',e=>{if(e.key===KEY&&CUR)side()});
if(CUR&&!localStorage.getItem('cdcsv_wl_'+me())){notify(me(),'Chào mừng bạn đến với Chợ đồ cũ sinh viên! Hãy đăng tin hoặc đặt mua món đầu tiên.','home','👋');localStorage.setItem('cdcsv_wl_'+me(),'1');save();side()}


/* extras.js – bổ sung cho trang chợ (index.html). Nạp SAU app.js. */

/* 1. Ẩn nút "Chat" (chưa có chức năng) */
document.querySelectorAll('header a, header button, .hd a, .hd button').forEach(e => {
  const t = e.textContent.trim();
  if (t.endsWith('Chat') && t.length < 12) e.style.display = 'none';
});

/* 2. Thanh sắp xếp: thêm "Giá thấp nhất", chia cột tự động */
const _renderRes = renderRes;
renderRes = function () {
  _renderRes();
  const t = document.querySelector('#res .card.tabs');
  if (t && t.querySelector('[onclick^="setSort"]')) {
    if (!t.querySelector(`[onclick="setSort('low')"]`))
      t.insertAdjacentHTML('beforeend', `<button class="tab ${S.sort === 'low' ? 'on' : ''}" onclick="setSort('low')">$ Giá thấp nhất</button>`);
    t.style.gridTemplateColumns = 'repeat(auto-fit,minmax(110px,1fr))';
  }
};

/* 3. Thay các số liệu giả bằng số liệu thật tính từ dữ liệu tin đăng */
function retitle(el, ic, txt) {
  const h = el && el.closest('.card') && el.closest('.card').querySelector('.sh');
  if (h) h.innerHTML = `<span>${ic}</span>${txt}`;
}
function realWidgets() {
  const approved = L.filter(l => l.st === 'approved');
  const sold = L.filter(l => l.st === 'sold');

  // 3a. "Tìm kiếm nhiều" -> danh mục có nhiều tin nhất
  const tr = $('#trend');
  if (tr) {
    const rows = CATS.map((c, i) => ({ i, n: c[0], k: approved.filter(l => l.c === i).length }))
      .sort((a, b) => b.k - a.k).slice(0, 5);
    tr.innerHTML = rows.map((r, j) => `<button class="tr" onclick="pickCat(${r.i})"><i>${j + 1}</i><span>${esc(r.n)}</span><span class="mut" style="flex:none">${r.k} tin</span></button>`).join('');
    retitle(tr, '🔥', 'Danh mục nhiều tin nhất');
  }

  // 3b. "Thống kê hôm nay" -> thống kê chợ
  const s1 = $('#s1');
  if (s1) {
    const card = s1.closest('.card');
    const stats = [...card.querySelectorAll('.stat')];
    stats.forEach((e, i) => { if (i > 0) e.remove(); });
    const sellers = new Set(approved.concat(sold).map(l => l.s)).size;
    stats[0].innerHTML = `Tin đang bán<b id="s1" style="color:var(--g)">${approved.length}</b>`;
    stats[0].insertAdjacentHTML('afterend',
      `<div class="stat">Đã bán<b>${sold.length}</b></div><div class="stat">Người bán<b>${sellers}</b></div>`);
    retitle(card.querySelector('.sh') ? card : s1, '📈', 'Thống kê chợ');
  }

  // 3c. "Đang trực tuyến" -> người bán nổi bật (nhiều tin nhất)
  const onl = $('#onl');
  if (onl) {
    const cnt = {};
    approved.forEach(l => { cnt[l.s] = (cnt[l.s] || 0) + 1; });
    const top = Object.entries(cnt).sort((a, b) => b[1] - a[1]).slice(0, 3);
    onl.innerHTML = top.length ? top.map(([id, k]) => {
      const sid = isNaN(id) ? id : +id, n = nm(sid);
      return `<div class="sel"><div class="av">${esc((n[0] || '?').toUpperCase())}</div><div><b>${esc(n)}</b><div class="mut">${k} tin đang bán · ${repTxt(sid)}</div></div></div>`;
    }).join('') : '<span class="mut">Chưa có người bán nào.</span>';
    retitle(onl, '🏅', 'Người bán nổi bật');
  }
}
const _side = side;
side = function () {
  _side();
  try { realWidgets(); } catch (e) { console.warn('realWidgets:', e); }
};

/* 4. "Tin của tôi": hiện lý do tin bị từ chối / bị ẩn */
const _mineHtml = mineHtml;
mineHtml = function () {
  const bad = L.filter(l => l.s === me() && l.st === 'hidden');
  const box = bad.length
    ? `<div class="card pad" style="border-color:#f0b4b4"><div class="hh" style="color:#b42318">Tin không được hiển thị (${bad.length})</div>${bad.map(l =>
        `<div style="padding:8px 0"><b>${esc(l.t)}</b><div class="mut">Lý do: ${esc(l.rr || 'Kiểm duyệt viên chưa ghi rõ lý do')}</div></div>`).join('')}</div>`
    : '';
  return box + _mineHtml();
};





/* ===== ĐÁNH GIÁ NGƯỜI BÁN SAU GIAO DỊCH ===== */
(function () {
  const s = document.createElement('style');
  s.textContent = '.rvs{background:none;border:0;font-size:34px;line-height:1;color:#d5dcd8;cursor:pointer;padding:0 2px}.rvs.on{color:#f5a623}.rvl{padding:10px 0;border-top:1px solid #e6ebe8}.rvl:first-child{border-top:0}.stars{color:#f5a623;letter-spacing:1px}';
  document.head.appendChild(s);
})();

let RV = { l: 0, offer: 0, star: 0 };
const RVTXT = ['Chọn số sao', 'Tệ', 'Chưa tốt', 'Bình thường', 'Tốt', 'Rất tốt'];

// Chỉ người MUA của tin đã bán (đề nghị được chấp nhận, hoặc đơn đã nhận hàng) và chưa đánh giá mới được đánh giá
function canReview(l) {
  const m = me();
  if (!CUR || !l || l.s === m) return false;
  const accepted = O.find(o => o.l === l.id && o.f === m && o.st === 'accepted');
  return !!accepted && !R.some(r => r.offer_id === accepted.id);
}
function repTxtL(lid) {
  const r = R.filter(x => x.l === lid);
  return r.length ? `★ ${(r.reduce((a, b) => a + b.star, 0) / r.length).toFixed(1)} (${r.length} đánh giá)` : 'Chưa có đánh giá';
}




function reviewsHtml(sid, lid) {
    const rs = R.filter(r => lid ? r.l === lid : r.to === sid).reverse().slice(0, 5);
  if (!rs.length) return '<div class="mut">Sản phẩm này chưa có đánh giá nào.</div>';
  return rs.map(r => `<div class="rvl"><div><span class="stars">${'★'.repeat(r.star)}${'☆'.repeat(5 - r.star)}</span> <b>${esc(nm(r.f))}</b></div><div class="mut">${esc(r.x)}</div></div>`).join('');
}
const _openDetail = openDetail;
openDetail = function (id) {
  _openDetail(id);
  const l = L.find(x => x.id === id), db = document.querySelector('#dlg .db');
  if (!l || !db) return;
  const sm = db.querySelector('.sel .mut');
if (sm) sm.textContent = repTxtL(l.id);
  const done = l.st === 'sold' && CUR && R.some(r => r.l === l.id && r.f === me());
  db.insertAdjacentHTML('beforeend',
    `<div class="box"><b>Đánh giá sản phẩm (${repTxtL(l.id)})</b>${reviewsHtml(l.s, l.id)}${
      canReview(l) ? `<button class="btn" onclick="openReview(${l.id})">★ Đánh giá người bán</button>`
      : done ? '<span class="badge">★ Bạn đã đánh giá giao dịch này</span>' : ''}</div>`);
};
function starBtns(n) {
  return [1, 2, 3, 4, 5].map(i => `<button type="button" class="rvs ${i <= n ? 'on' : ''}" aria-label="${i} sao" onclick="pickStar(${i})">★</button>`).join('');
}
function openReview(lid) {
  const l = L.find(x => x.id === lid);
  if (!canReview(l)) return toast('Bạn chưa thể đánh giá giao dịch này.');
  const accepted = O.find(o => o.l === lid && o.f === me() && o.st === 'accepted');
  if (!accepted) return toast('Không tìm thấy đề nghị đã được chấp nhận để đánh giá.');
  RV = { l: lid, offer: accepted.id, star: 0 };
  openDlg(`${dh('Đánh giá người bán')}<div class="db">
   <div class="sel"><div class="av">${esc(nm(l.s)[0])}</div><div><b>${esc(nm(l.s))}</b><div class="mut">Giao dịch: ${esc(l.t)}</div></div></div>
   <div class="f" id="rvf1">Mức độ hài lòng *<div id="rvst">${starBtns(0)}</div><span class="mut" id="rvlb">${RVTXT[0]}</span><span class="err"></span></div>
   <label class="f" id="rvf2">Nhận xét *<textarea id="rvx" rows="3" maxlength="300" placeholder="Đồ đúng mô tả, giao dịch nhanh, hẹn đúng giờ..."></textarea><span class="err"></span></label>
   <button class="btn" onclick="submitRv()">Gửi đánh giá</button></div>`);
}
function pickStar(n) { RV.star = n; $('#rvst').innerHTML = starBtns(n); $('#rvlb').textContent = RVTXT[n]; }
async function submitRv() {
  const l = L.find(x => x.id === RV.l);
  const bad = (id, m) => { const f = $('#' + id); f.classList.add('bad'); f.querySelector('.err').textContent = m; return 1; };
  ['rvf1', 'rvf2'].forEach(i => { $('#' + i).classList.remove('bad'); $('#' + i).querySelector('.err').textContent = ''; });
  const x = $('#rvx').value.trim();
  let e = 0;
  if (!RV.star) e += bad('rvf1', 'Vui lòng chọn số sao từ 1 đến 5.');
  if (x.length < 3) e += bad('rvf2', 'Nhận xét cần ít nhất 3 ký tự.');
  if (e) return;
  if (!l || !RV.offer) return toast('Không tìm thấy giao dịch hợp lệ để đánh giá.');
  try {
    await api('/offers/' + RV.offer + '/review', {
      method: 'POST',
      body: JSON.stringify({ rating: RV.star, comment: x })
    });
    $('#dlg').close();
    toast('Đã gửi đánh giá lên máy chủ.');
    await loadFromApi();
    refresh(true);
  } catch (err) { toast(err.message); }
}
// Nút "Đánh giá" ở trang Đơn hàng cũng dùng form mới
reviewForm = function (oid) { const o = ORD.find(x => x.id === oid); if (o) openReview(o.l); };



/* ===== SỬA ĐÁNH GIÁ ===== */

// Danh sách đánh giá: thêm nhãn "đã chỉnh sửa"
reviewsHtml = function (sid, lid) {
  const rs = R.filter(r => r.to === sid && (!lid || r.l === lid)).reverse().slice(0, 5);
  if (!rs.length) return '<div class="mut">Sản phẩm này chưa có đánh giá nào.</div>';
  return rs.map(r => `<div class="rvl"><div><span class="stars">${'★'.repeat(r.star)}${'☆'.repeat(5 - r.star)}</span> <b>${esc(nm(r.f))}</b></div><div class="mut">${esc(r.x)}</div></div>`).join('');
};

// Trang chi tiết sản phẩm: người đã đánh giá thấy nút "Sửa đánh giá"
const _openDetail2 = openDetail;
openDetail = function (id) {
  _openDetail2(id);
  const l = L.find(x => x.id === id), db = document.querySelector('#dlg .db');
  if (!l || !db || !CUR) return;
  if (!R.some(r => r.l === l.id && r.f === me())) return;
  const box = db.lastElementChild;
  if (box && !box.querySelector('[data-edit-rv]'))
    box.insertAdjacentHTML('beforeend', `<button class="btn o sm" data-edit-rv onclick="editReview(${l.id})">✎ Sửa đánh giá của tôi</button>`);
};

// Trang Đơn hàng: thêm nút "Sửa đánh giá" cạnh nhãn "Đã đánh giá"
const _orderCard = orderCard;
orderCard = function (o) {
  let h = _orderCard(o);
  if (o.rv && o.b === me())
    h = h.replace('<span class="badge">★ Đã đánh giá</span>',
      `<span class="badge">★ Đã đánh giá</span><button class="btn sm o" onclick="editReview(${o.l})">✎ Sửa đánh giá</button>`);
  return h;
};

function editReview(lid) {
  const l = L.find(x => x.id === lid), r = R.find(x => x.l === lid && x.f === me());
  if (!l || !r) return toast('Không tìm thấy đánh giá để sửa.');
  RV = { l: lid, star: r.star };
  openDlg(`${dh('Sửa đánh giá')}<div class="db">
   <div class="sel"><div class="av">${esc(nm(l.s)[0])}</div><div><b>${esc(nm(l.s))}</b><div class="mut">Sản phẩm: ${esc(l.t)}</div></div></div>
   <div class="f" id="rvf1">Mức độ hài lòng *<div id="rvst">${starBtns(r.star)}</div><span class="mut" id="rvlb">${RVTXT[r.star]}</span><span class="err"></span></div>
   <label class="f" id="rvf2">Nhận xét *<textarea id="rvx" rows="3" maxlength="300">${esc(r.x)}</textarea><span class="err"></span></label>
   <div class="row"><button class="btn o" style="flex:1" onclick="openDetail(${lid})">← Quay lại</button><button class="btn" style="flex:2" onclick="submitEditRv()">Lưu thay đổi</button></div></div>`);
}

function submitEditRv() {
  const l = L.find(x => x.id === RV.l), r = R.find(x => x.l === RV.l && x.f === me());
  if (!l || !r) return toast('Bạn không có quyền sửa đánh giá này (403).');
  const bad = (id, m) => { const f = $('#' + id); f.classList.add('bad'); f.querySelector('.err').textContent = m; return 1; };
  ['rvf1', 'rvf2'].forEach(i => { $('#' + i).classList.remove('bad'); $('#' + i).querySelector('.err').textContent = ''; });
  const x = $('#rvx').value.trim();
  let e = 0;
  if (!RV.star) e += bad('rvf1', 'Vui lòng chọn số sao từ 1 đến 5.');
  if (x.length < 10) e += bad('rvf2', 'Nhận xét cần ít nhất 10 ký tự.');
  if (e) return;
  r.star = RV.star; r.x = x; r.ed = Date.now();
  notify(l.s, `${nm(me())} đã cập nhật đánh giá thành ${RV.star} sao cho "${l.t}"`, 'home', '⭐');
  openDetail(l.id);
  toast('Đã cập nhật đánh giá.');
  refresh(true);
}


/* ===== ĐỒNG BỘ SỐ ĐẾM VÀ DANH SÁCH ĐÁNH GIÁ ===== */
function reviewsOf(lid) {
  const l = L.find(x => x.id === lid);
  return l ? R.filter(r => r.to === l.s) : [];
}
repTxtL = function (lid) {
  const r = reviewsOf(lid);
  return r.length
    ? `★ ${(r.reduce((a, b) => a + b.star, 0) / r.length).toFixed(1)} (${r.length} đánh giá)`
    : 'Chưa có đánh giá';
};
reviewsHtml = function (sid, lid) {
  const rs = reviewsOf(lid).reverse().slice(0, 5);
  if (!rs.length) return '<div class="mut">Sản phẩm này chưa có đánh giá nào.</div>';
  return rs.map(r => `<div class="rvl"><div><span class="stars">${'★'.repeat(r.star)}${'☆'.repeat(5 - r.star)}</span> <b>${esc(nm(r.f))}</b>${r.ed ? ' <span class="mut">· đã chỉnh sửa</span>' : ''}</div><div class="mut">${esc(r.x)}</div></div>`).join('');
};

/* ===== ĐĂNG TIN LƯU VÀO BACKEND ===== */
let picFiles = [];
let posting = false;

const _openPost = openPost;
openPost = function () { picFiles = []; _openPost(); };

pickImgs = function (inp) {
  const fs = [...inp.files].slice(0, 5);
  picFiles = fs; pics = [];
  $('#th').innerHTML = '';
  fs.forEach(f => {
    const r = new FileReader();
    r.onload = () => { pics.push(r.result); $('#th').insertAdjacentHTML('beforeend', `<img src="${r.result}" alt="">`); };
    r.readAsDataURL(f);
  });
};

submitPost = async function () {
  const bad = (id, m) => { const f = $('#' + id); f.classList.add('bad'); f.querySelector('.err').textContent = m; return 1; };
  ['pt', 'pp', 'pc', 'pi'].forEach(i => { $('#' + i).classList.remove('bad'); $('#' + i).querySelector('.err').textContent = ''; });
  const t = $('#pti').value.trim(), p = +$('#ppr').value, c = $('#pca').value;
  let e = 0;
  if (t.length < 5) e += bad('pt', 'Tiêu đề cần ít nhất 5 ký tự.');
  if (!Number.isInteger(p) || p < 1000) e += bad('pp', 'Giá phải là số nguyên từ 1.000đ trở lên.');
  if (c === '') e += bad('pc', 'Hãy chọn danh mục.');
  if (!picFiles.length) e += bad('pi', 'Cần ít nhất 1 ảnh.');
  if (e || posting) return;
  if (!getToken()) { alert('Bạn cần đăng nhập (hoặc đăng ký tài khoản mới) để đăng tin.'); location.href = 'login.html#login'; return; }
  posting = true;
  try {
    const body = {
      title: t, price: p, category_id: CAT_IDS[+c],
      condition: ['like_new', 'good', 'fair'][+$('#pk').value] || 'good',
      description: $('#pd').value.trim() || 'Không có mô tả.'
    };
    const created = await api('/listings', { method: 'POST', body: JSON.stringify(body) });
    const fd = new FormData();
    picFiles.forEach(f => fd.append('files', f));
    await api(`/listings/${created.id}/images`, { method: 'POST', body: fd });
    await loadFromApi();
    $('#dlg').close();
    toast('Đã gửi tin. Tin sẽ hiển thị sau khi kiểm duyệt viên duyệt.');
    go('mine');
  } catch (err) {
    alert('Lỗi đăng tin: ' + (err.message || err));
  } finally { posting = false; }
};




/* ===== TỰ CẬP NHẬT DỮ LIỆU TỪ BACKEND (30 giây) ===== */
let syncing = false;
async function autoSync() {
  if (syncing || document.hidden || posting) return;
  const d = $('#dlg');
  if (d && d.open) return;              // đang mở hộp thoại thì không làm phiền
  syncing = true;
  try { await loadFromApi(); refresh(); } catch (e) { /* lần sau thử lại */ }
  finally { syncing = false; }
}
setInterval(autoSync, 30000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) autoSync(); });

// Backend hiện chỉ hỗ trợ tạo và đọc đánh giá; không giả lập sửa đánh giá ở local.
editReview = function () { toast('Backend hiện chưa cung cấp chức năng sửa đánh giá.'); };
