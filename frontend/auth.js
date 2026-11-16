/* Xác thực: ưu tiên backend FastAPI (localhost:8001), dự phòng bằng localStorage (tài khoản demo). */
const UKEY='cdcsv_users',SKEY='cdcsv_session',AKEY='cdcsv_admin';
const GOOGLE_CLIENT_ID=''; // Dán Client ID lấy từ Google Cloud Console vào đây để dùng đăng nhập Google thật
const ADMIN={email:'admin@demo.vn',pw:'admin123'};
const AUTH_API=(location.port==="5500"?"http://localhost:8001":"")+"/api/v1",AUTH_TOKEN_KEY="cdcsv_token",AUTH_BUSER_KEY="cdcsv_buser";

async function sha(p){
  try{const b=await crypto.subtle.digest('SHA-256',new TextEncoder().encode('cdcsv:'+p));return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')}
  catch(e){let h=5381;for(const c of 'cdcsv:'+p)h=(h*33^c.charCodeAt(0))>>>0;return 'x'+h}
}
function getUsers(){try{return JSON.parse(localStorage.getItem(UKEY)||'[]')}catch(e){return[]}}
function putUsers(a){localStorage.setItem(UKEY,JSON.stringify(a))}
async function seedUsers(){
  if(getUsers().length)return;
  const h=await sha('123456');
  putUsers([['u1','Nguyễn Văn An','an@demo.vn','SV0001'],['u2','Minh Anh','minhanh@demo.vn','SV0002'],['u3','Hoàng Long','long@demo.vn','SV0003'],['u4','Thu Hà','ha@demo.vn','SV0004']]
    .map(([id,name,email,mssv])=>({id,name,email,mssv,phone:'0900000000',pw:h})));
}

function session(){
  try{
    const b=localStorage.getItem(AUTH_BUSER_KEY);
    if(b&&localStorage.getItem(AUTH_TOKEN_KEY))return JSON.parse(b);
    const id=localStorage.getItem(SKEY);
    return id?getUsers().find(u=>u.id===id)||null:null
  }catch(e){return null}
}
function logout(){
  [SKEY,AUTH_TOKEN_KEY,AUTH_BUSER_KEY,AKEY].forEach(k=>localStorage.removeItem(k))
}
function authBearerHeader(){const t=localStorage.getItem(AUTH_TOKEN_KEY);return t?{Authorization:'Bearer '+t}:{}}

async function register(v){
  await seedUsers();
  const e={},name=(v.name||'').trim(),email=(v.email||'').trim().toLowerCase(),mssv=(v.mssv||'').trim(),phone=(v.phone||'').replace(/\s/g,'');
  if(name.length<2)e.name='Nhập họ và tên (ít nhất 2 ký tự).';
  if(!/^[A-Za-z0-9]{6,12}$/.test(mssv))e.mssv='MSSV gồm 6–12 chữ hoặc số.';
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))e.email='Email không hợp lệ.';
  else if(getUsers().some(u=>u.email===email))e.email='Email này đã được đăng ký.';
  if(!/^(0|\+84)\d{9}$/.test(phone))e.phone='Số điện thoại không hợp lệ (ví dụ 0912345678).';
  if(!v.pw||v.pw.length<8||!/[A-Za-z]/.test(v.pw)||!/\d/.test(v.pw))e.pw='Mật khẩu ít nhất 8 ký tự, gồm cả chữ và số.';
  if(v.pw2!==v.pw)e.pw2='Mật khẩu nhập lại không khớp.';
  if(!v.agree)e.agree='Bạn cần đồng ý với điều khoản.';
  if(Object.keys(e).length)return{ok:false,errors:e};
  const u={id:'u'+Date.now().toString(36),name,email,mssv,phone,pw:await sha(v.pw)};
  putUsers([...getUsers(),u]);localStorage.setItem(SKEY,u.id);return{ok:true}
}

/* Đăng nhập tài khoản demo lưu trong trình duyệt (dự phòng) */
async function authLoginLocal(email,pw){
  await seedUsers();
  const u=getUsers().find(x=>x.email===email.toLowerCase());
  if(!u||!u.pw||u.pw!==await sha(pw))return{ok:false,field:'pw',msg:'Email hoặc mật khẩu không đúng.'};
  localStorage.removeItem(AUTH_TOKEN_KEY);localStorage.removeItem(AUTH_BUSER_KEY);
  localStorage.setItem(SKEY,u.id);return{ok:true,role:'student'}
}

async function authFetchMe(tk){
  for(const p of ['/users/me','/auth/me']){
    try{
      const r=await fetch(AUTH_API+p,{headers:{Authorization:'Bearer '+tk}});
      if(r.ok)return await r.json()
    }catch(e){}
  }
  return null
}

/* Đăng nhập backend: gửi form lên POST /auth/login */
async function login(email,pw){
  if(!email)return{ok:false,field:'email',msg:'Nhập email.'};
  if(!pw)return{ok:false,field:'pw',msg:'Nhập mật khẩu.'};
  email=email.trim();
  let res;
  try{
    res=await fetch(AUTH_API+'/auth/login',{
      method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body:new URLSearchParams({username:email,password:pw})
    });
  }catch(e){
    console.warn('Không gọi được backend (mạng/CORS):',e);
    return authLoginLocal(email,pw);
  }
  if(!res.ok){
    console.warn('Backend trả về',res.status,await res.text());
    return authLoginLocal(email,pw);
  }
  const {access_token}=await res.json();
  localStorage.setItem(AUTH_TOKEN_KEY,access_token);
  const me=(await authFetchMe(access_token))||{};
  const role=String(me.role||'student').toLowerCase();
  const u={
    id:(me.id!==undefined&&me.id!==null?me.id:email),
    name:me.full_name||me.name||email.split('@')[0],
    email:me.email||email.toLowerCase(),
    mssv:me.student_id||me.mssv||'',
    phone:me.phone||'',
    role,backend:true
  };
  localStorage.setItem(AUTH_BUSER_KEY,JSON.stringify(u));
  if(role==='admin'||role.startsWith('mod'))localStorage.setItem(AKEY,'1');
  return{ok:true,role}
}

async function loginGoogle(p){
  await seedUsers();
  const email=(p.email||'').toLowerCase();let u=getUsers().find(x=>x.email===email);
  if(!u){u={id:'g'+Date.now().toString(36),name:p.name||email.split('@')[0],email,mssv:'',phone:'',pw:'',google:true};putUsers([...getUsers(),u])}
  localStorage.setItem(SKEY,u.id);return{ok:true}
}
function decodeJwt(t){const b=t.split('.')[1].replace(/-/g,'+').replace(/_/g,'/');return JSON.parse(decodeURIComponent(escape(atob(b))))}
function adminLogin(e,p){if(e.toLowerCase()===ADMIN.email&&p===ADMIN.pw){localStorage.setItem(AKEY,'1');return true}return false}
function adminLogout(){localStorage.removeItem(AKEY)}