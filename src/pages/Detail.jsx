import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api, { errMsg, money, STATUS } from "../api.js";
import { useAuth } from "../auth.jsx";
export default function Detail() {
  const { id } = useParams(); const { user } = useAuth();
  const [l, setL] = useState(null); const [err, setErr] = useState(""); const [msg, setMsg] = useState(""); const [img, setImg] = useState(0);
  const [offer, setOffer] = useState({ price: "", message: "" });
  useEffect(() => { api.get(`/listings/${id}`).then(r => { setL(r.data); setOffer(o => ({ ...o, price: r.data.price })); }).catch(e => setErr(errMsg(e))); }, [id]);
  const send = async (fn, ok) => { setErr(""); setMsg(""); try { await fn(); setMsg(ok); } catch (e) { setErr(errMsg(e)); } };
  if (err && !l) return <div className="wrap"><p className="err">{err}</p></div>;
  if (!l) return <div className="wrap"><p className="muted">Đang tải…</p></div>;
  const mine = user?.id === l.seller?.id;
  return (<div className="wrap detail">
    <div><div className="big">{l.images?.[img] ? <img src={l.images[img].url} alt={l.title} /> : <span>Chưa có ảnh</span>}</div>
      <div className="strip">{l.images?.map((im, i) => <img key={i} src={im.url} className={i === img ? "on" : ""} onClick={() => setImg(i)} alt="" />)}</div></div>
    <div><h1>{l.title}</h1><span className="tag lg">{money(l.price)}</span>
      <p className="muted">{l.condition} · {l.category?.name} · {STATUS[l.status]}</p><p>{l.description}</p>
      <p>Người bán: <b>{l.seller?.full_name}</b>{l.seller?.reputation != null && <> – uy tín {Number(l.seller.reputation).toFixed(1)}/5</>}</p>
      {msg && <p className="ok">{msg}</p>}{err && <p className="err">{err}</p>}
      {l.status === "approved" && !mine && (user ? <div className="box"><h3>Gửi đề nghị mua</h3>
        <input type="number" min="1" value={offer.price} onChange={e => setOffer({ ...offer, price: e.target.value })} />
        <textarea placeholder="Lời nhắn cho người bán" value={offer.message} onChange={e => setOffer({ ...offer, message: e.target.value })} />
        <button className="btn" onClick={() => send(() => api.post(`/listings/${id}/offers`, { price: Number(offer.price), message: offer.message }), "Đã gửi đề nghị. Người bán sẽ phản hồi.")}>Gửi đề nghị</button></div>
        : <p><Link to="/login">Đăng nhập</Link> để gửi đề nghị mua.</p>)}
      {user && !mine && <button className="ghost" onClick={() => { const r = prompt("Lý do báo cáo tin này:"); r && send(() => api.post(`/listings/${id}/reports`, { reason: r }), "Đã gửi báo cáo. Kiểm duyệt viên sẽ xem xét."); }}>Báo cáo vi phạm</button>}
    </div></div>);
}
