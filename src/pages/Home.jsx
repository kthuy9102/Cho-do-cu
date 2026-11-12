import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api, { errMsg, money } from "../api.js";
export default function Home() {
  const [sp, setSp] = useSearchParams();
  const [cats, setCats] = useState([]); const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true); const [err, setErr] = useState("");
  const q = Object.fromEntries(sp); const page = Number(q.page || 1); const size = 12;
  const set = (k, v) => { const n = new Map(sp); v ? n.set(k, v) : n.delete(k); if (k !== "page") n.delete("page"); setSp(n); };
  useEffect(() => { api.get("/categories").then(r => setCats(r.data)).catch(() => {}); }, []);
  useEffect(() => {
    setLoading(true); setErr("");
    api.get("/listings", { params: { q: q.q, category_id: q.category, min_price: q.min, max_price: q.max, sort: q.sort || "newest", page, size } })
      .then(r => setData(r.data)).catch(e => setErr(errMsg(e))).finally(() => setLoading(false));
  }, [sp]);
  const pages = Math.max(1, Math.ceil(data.total / size));
  return (<div className="wrap">
    <section className="hero"><h1>Đồ dùng sau kỳ thi, tìm người cần tiếp theo.</h1>
      <input className="search" placeholder="Tìm giáo trình, máy tính, quạt…" defaultValue={q.q} onKeyDown={e => e.key === "Enter" && set("q", e.target.value.trim())} /></section>
    <div className="filters">
      <select value={q.category || ""} onChange={e => set("category", e.target.value)}><option value="">Tất cả danh mục</option>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
      <input type="number" min="0" placeholder="Giá từ" defaultValue={q.min} onBlur={e => set("min", e.target.value)} />
      <input type="number" min="0" placeholder="Giá đến" defaultValue={q.max} onBlur={e => set("max", e.target.value)} />
      <select value={q.sort || "newest"} onChange={e => set("sort", e.target.value)}><option value="newest">Mới nhất</option><option value="price_asc">Giá tăng dần</option><option value="price_desc">Giá giảm dần</option></select>
    </div>
    {err && <p className="err">{err}</p>}
    {loading ? <p className="muted">Đang tải…</p> : data.items.length === 0 && !err ? <p className="muted">Chưa có tin nào khớp. Thử bỏ bớt bộ lọc, hoặc đăng tin đầu tiên.</p> :
      <div className="grid">{data.items.map(l => (
        <Link to={`/listings/${l.id}`} className="card" key={l.id}>
          <div className="thumb">{l.images?.[0] ? <img src={l.images[0].url} alt={l.title} /> : <span>Chưa có ảnh</span>}</div>
          <div className="body"><h3>{l.title}</h3><small>{l.condition}</small><span className="tag">{money(l.price)}</span></div>
        </Link>))}</div>}
    <div className="pager"><button className="ghost" disabled={page <= 1} onClick={() => set("page", page - 1)}>Trước</button>
      <span>Trang {page}/{pages}</span><button className="ghost" disabled={page >= pages} onClick={() => set("page", page + 1)}>Sau</button></div>
  </div>);
}
