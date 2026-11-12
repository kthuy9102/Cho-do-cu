import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { errMsg } from "../api.js";
export default function Create() {
  const nav = useNavigate(); const [cats, setCats] = useState([]); const [files, setFiles] = useState([]); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const [f, setF] = useState({ title: "", description: "", price: "", condition: "Như mới", category_id: "" });
  useEffect(() => { api.get("/categories").then(r => setCats(r.data)).catch(() => {}); }, []);
  const pick = e => {
    const list = [...e.target.files];
    if (list.length > 5) return setErr("Tối đa 5 ảnh.");
    if (list.some(x => !x.type.startsWith("image/") || x.size > 5 * 1024 * 1024)) return setErr("Chỉ nhận file ảnh, mỗi ảnh tối đa 5 MB.");
    setErr(""); setFiles(list);
  };
  const submit = async e => {
    e.preventDefault(); setErr("");
    if (f.title.trim().length < 5) return setErr("Tiêu đề cần ít nhất 5 ký tự.");
    if (!(Number(f.price) > 0)) return setErr("Giá phải lớn hơn 0.");
    if (!f.category_id) return setErr("Chọn danh mục.");
    if (!files.length) return setErr("Thêm ít nhất 1 ảnh.");
    const d = new FormData(); Object.entries(f).forEach(([k, v]) => d.append(k, v)); files.forEach(x => d.append("images", x));
    setBusy(true);
    try { await api.post("/listings", d); alert("Đã gửi tin. Tin sẽ hiển thị sau khi kiểm duyệt viên duyệt."); nav("/mine"); }
    catch (e) { setErr(errMsg(e)); } finally { setBusy(false); }
  };
  const on = k => e => setF({ ...f, [k]: e.target.value });
  return (<div className="wrap narrow"><h1>Đăng tin bán</h1><form onSubmit={submit} className="form">
    <label>Tiêu đề<input value={f.title} onChange={on("title")} /></label>
    <label>Mô tả<textarea value={f.description} onChange={on("description")} /></label>
    <label>Giá (đ)<input type="number" min="1" value={f.price} onChange={on("price")} /></label>
    <label>Tình trạng<select value={f.condition} onChange={on("condition")}><option>Mới</option><option>Như mới</option><option>Đã dùng</option><option>Cũ</option></select></label>
    <label>Danh mục<select value={f.category_id} onChange={on("category_id")}><option value="">Chọn…</option>{cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
    <label>Ảnh (tối đa 5)<input type="file" accept="image/*" multiple onChange={pick} /></label>
    <div className="strip">{files.map((x, i) => <img key={i} src={URL.createObjectURL(x)} alt="" />)}</div>
    {err && <p className="err">{err}</p>}<button className="btn" disabled={busy}>{busy ? "Đang gửi…" : "Gửi tin để duyệt"}</button></form></div>);
}
