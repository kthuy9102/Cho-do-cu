import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errMsg, money, STATUS } from "../api.js";
function useLoad(url) {
  const [d, setD] = useState(null); const [err, setErr] = useState("");
  const load = () => api.get(url).then(r => setD(r.data)).catch(e => setErr(errMsg(e)));
  useEffect(() => { load(); }, []); return [d, err, load];
}
export function Mine() {
  const [mine, e1] = useLoad("/listings/mine"); const [offers, e2, reload] = useLoad("/offers/received");
  const act = async (id, status) => { try { await api.patch(`/offers/${id}`, { status }); reload(); } catch (e) { alert(errMsg(e)); } };
  return (<div className="wrap"><h1>Tin của tôi</h1>{(e1 || e2) && <p className="err">{e1 || e2}</p>}
    {mine?.length === 0 && <p className="muted">Bạn chưa đăng tin nào.</p>}
    <div className="list">{mine?.map(l => <Link to={`/listings/${l.id}`} className="row" key={l.id}><b>{l.title}</b><span>{money(l.price)}</span><span className={`pill ${l.status}`}>{STATUS[l.status]}</span></Link>)}</div>
    <h2>Đề nghị mua nhận được</h2>{offers?.length === 0 && <p className="muted">Chưa có đề nghị nào.</p>}
    <div className="list">{offers?.map(o => <div className="row" key={o.id}><span><b>{o.buyer?.full_name}</b> đề nghị {money(o.price)} cho “{o.listing?.title}”<br /><small>{o.message}</small></span>
      {o.status === "pending" ? <span><button className="btn sm" onClick={() => act(o.id, "accepted")}>Chấp nhận</button> <button className="ghost" onClick={() => act(o.id, "rejected")}>Từ chối</button></span> : <span className="pill">{o.status === "accepted" ? "Đã chấp nhận" : "Đã từ chối"}</span>}</div>)}</div></div>);
}
export function Moderation() {
  const [pend, e1, r1] = useLoad("/listings/pending"); const [reps, e2, r2] = useLoad("/reports");
  const mod = async (id, status) => { try { await api.patch(`/listings/${id}/moderate`, { status }); r1(); } catch (e) { alert(errMsg(e)); } };
  const takedown = async (rep) => { try { await api.patch(`/listings/${rep.listing_id}/moderate`, { status: "rejected" }); await api.patch(`/reports/${rep.id}`, { status: "resolved" }); r2(); } catch (e) { alert(errMsg(e)); } };
  return (<div className="wrap"><h1>Kiểm duyệt</h1>{(e1 || e2) && <p className="err">{e1 || e2}</p>}
    <h2>Tin chờ duyệt</h2>{pend?.length === 0 && <p className="muted">Không còn tin nào chờ duyệt.</p>}
    <div className="list">{pend?.map(l => <div className="row" key={l.id}><Link to={`/listings/${l.id}`}><b>{l.title}</b> – {money(l.price)}</Link>
      <span><button className="btn sm" onClick={() => mod(l.id, "approved")}>Duyệt</button> <button className="ghost" onClick={() => mod(l.id, "rejected")}>Từ chối</button></span></div>)}</div>
    <h2>Báo cáo vi phạm</h2>{reps?.length === 0 && <p className="muted">Chưa có báo cáo nào.</p>}
    <div className="list">{reps?.map(r => <div className="row" key={r.id}><span><Link to={`/listings/${r.listing_id}`}>Tin #{r.listing_id}</Link>: {r.reason}</span>
      <span><button className="btn sm" onClick={() => takedown(r)}>Gỡ tin</button></span></div>)}</div></div>);
}
