/* Dữ liệu khởi tạo giao diện (fallback) cho trang chợ và quản trị.
   Dữ liệu nghiệp vụ thực tế được api.js đồng bộ từ Backend; localStorage chỉ còn phục vụ
   trạng thái giao diện/tương thích dữ liệu cũ, không phải nguồn dữ liệu chính. */
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const nz=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase();
const vnd=n=>Number(n).toLocaleString('vi-VN')+'đ';
const ago=d=>d<1?'Hôm nay':d<7?d+' ngày trước':d<30?Math.floor(d/7)+' tuần trước':Math.floor(d/30)+' tháng trước';
const CATS=[['Đồ điện tử','📱'],['Đồ dùng học tập','✏️'],['Đồ gia dụng','🍳'],['Sách & Tài liệu','📚'],['Thời trang','🧥']];
const CONDS=['Mới 99%','Đã dùng, còn tốt','Cũ, dùng được'];
const U={u1:{n:'Nguyễn Văn An',h:'@an'},u2:{n:'Minh Anh',h:'@minhanh'},u3:{n:'Hoàng Long',h:'@long'},u4:{n:'Thu Hà',h:'@ha'}};
let L=[
{id:1,t:'iPhone 11 64GB trắng',p:6200000,c:0,k:1,s:'u1',a:7,n:5,st:'approved',e:'📱',ds:'Máy dùng 2 năm, pin 86%, không trầy màn hình. Kèm sạc.'},
{id:2,t:'Giày MLB size 42',p:850000,c:4,k:0,s:'u2',a:7,n:3,st:'approved',e:'👟',ds:'Mua nhầm size, mới đi 2 lần. Còn hộp.'},
{id:3,t:'Tai nghe không dây',p:420000,c:0,k:1,s:'u3',a:7,n:2,st:'approved',e:'🎧',ds:'Âm thanh tốt, pin dùng được 4 giờ.'},
{id:4,t:'Giáo trình Giải tích 1',p:45000,c:3,k:2,s:'u4',a:2,n:2,st:'approved',e:'📘',ds:'Có ghi chú bút chì, đủ trang.'},
{id:5,t:'Macbook Air M1 2020',p:13500000,c:0,k:1,s:'u3',a:1,n:4,st:'approved',e:'💻',ds:'8GB/256GB, sạc 210 lần, ngoại hình đẹp.'},
{id:6,t:'Bàn phím cơ Keychron K2',p:1200000,c:0,k:0,s:'u2',a:3,n:3,st:'approved',e:'⌨️',ds:'Switch brown, bluetooth, đèn nền trắng.'},
{id:7,t:'Áo khoác bomber đen',p:180000,c:4,k:1,s:'u4',a:4,n:2,st:'approved',e:'🧥',ds:'Size M, giặt sạch, không bung chỉ.'},
{id:8,t:'Nồi cơm điện mini 1L',p:150000,c:2,k:1,s:'u2',a:10,n:2,st:'approved',e:'🍚',ds:'Phù hợp ký túc xá, dùng 1 học kỳ.'},
{id:9,t:'Bàn học gấp gọn',p:220000,c:2,k:1,s:'u3',a:12,n:3,st:'approved',e:'🪑',ds:'Gấp gọn, mặt bàn 60x40cm.'},
{id:10,t:'Máy tính Casio fx-580VN X',p:350000,c:1,k:0,s:'u4',a:5,n:2,st:'approved',e:'🧮',ds:'Còn hộp và sách hướng dẫn.'},
{id:11,t:'Sách Lập trình Python cơ bản',p:60000,c:3,k:1,s:'u2',a:0,n:1,st:'approved',e:'🐍',ds:'Sách giáo trình học phần Python.'},
{id:12,t:'Laptop Dell Inspiron 15',p:7800000,c:0,k:1,s:'u3',a:20,n:4,st:'sold',e:'💻',ds:'Core i5, 8GB RAM, SSD 256GB.'},
{id:13,t:'Ghế xoay văn phòng',p:300000,c:2,k:1,s:'u4',a:0,n:2,st:'pending',e:'🪑',ds:'Chân sắt, tựa lưng lưới.'},
{id:14,t:'Đèn học LED chống cận',p:90000,c:1,k:0,s:'u2',a:6,n:2,st:'approved',e:'💡',ds:'3 mức sáng, cổng USB.'},
{id:15,t:'Balo laptop chống sốc',p:190000,c:4,k:1,s:'u3',a:9,n:2,st:'approved',e:'🎒',ds:'Vừa laptop 15.6 inch.'}];
let O=[{id:1,l:1,f:'u3',p:5900000,m:'Bạn bớt chút được không, mình lấy luôn.',st:'pending'},{id:2,l:12,f:'u1',p:7500000,m:'',st:'accepted'}];
let R=[{l:12,to:'u3',f:'u4',star:5,x:'Giao dịch nhanh, đúng mô tả.'},{l:5,to:'u3',f:'u2',star:4,x:'Máy đẹp.'},{l:2,to:'u2',f:'u3',star:5,x:'Người bán thân thiện.'},{l:4,to:'u4',f:'u2',star:4,x:'Sách sạch sẽ.'}];
let RP=[{id:1,l:15,f:'u4',x:'Ảnh không đúng sản phẩm',open:true}];

const _n=Date.now(),DAY=864e5;
/* Đơn hàng. st: pending (chờ xác nhận) → confirmed (đã xác nhận) → shipping (đang giao) → done (đã nhận), hoặc cancelled */
let ORD=[{id:1,code:'DH100231',l:12,b:'u1',s:'u3',p:7500000,name:'Nguyễn Văn An',phone:'0900000000',addr:'KTX khu A, phòng 305',pay:'Gặp trực tiếp tại trường / Kiểm tra hàng rồi trả tiền',note:'',st:'shipping',ts:{pending:_n-2*DAY,confirmed:_n-DAY,shipping:_n-3600e3},eta:_n+DAY}];
/* Thông báo: to = id người nhận, link = trang mở khi bấm (home, mine, saved, orders, orders:sell) */
let NOTI=[];
function notify(to,t,link,ic){NOTI.push({id:NOTI.length?Math.max(...NOTI.map(x=>x.id))+1:1,to,t,link:link||'home',ic:ic||'🔔',ts:Date.now(),read:false})}
const KEY='cdcsv_v2';
function loadData(){try{const d=JSON.parse(localStorage.getItem(KEY)||'null');if(d){L=d.L;O=d.O;R=d.R;RP=d.RP;if(d.ORD)ORD=d.ORD;if(d.NOTI)NOTI=d.NOTI}}catch(e){}}
function saveData(){try{localStorage.setItem(KEY,JSON.stringify({L,O,R,RP,ORD,NOTI}));return true}catch(e){return false}}
function resetData(){localStorage.removeItem(KEY);location.reload()}
loadData();