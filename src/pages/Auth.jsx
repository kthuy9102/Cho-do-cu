import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api, { errMsg } from "../api.js";
import { useAuth } from "../auth.jsx";
export default function Auth({ mode }) {
  const reg = mode === "register"; const nav = useNavigate(); const { login } = useAuth();
  const [f, setF] = useState({ full_name: "", email: "", password: "" }); const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const submit = async e => {
    e.preventDefault(); setErr("");
    if (!/^\S+@\S+\.\S+$/.test(f.email)) return setErr("Email chưa đúng định dạng.");
    if (f.password.length < 8) return setErr("Mật khẩu cần ít nhất 8 ký tự.");
    if (reg && !f.full_name.trim()) return setErr("Nhập họ tên của bạn.");
    setBusy(true);
    try {
      if (reg) await api.post("/auth/register", f);
      const r = await api.post("/auth/login", { email: f.email, password: f.password });
      login(r.data.access_token, r.data.user); nav("/");
    } catch (e) { setErr(errMsg(e)); } finally { setBusy(false); }
  };
  return (<div className="wrap narrow"><h1>{reg ? "Tạo tài khoản" : "Đăng nhập"}</h1>
    <form onSubmit={submit} className="form">
      {reg && <label>Họ tên<input value={f.full_name} onChange={e => setF({ ...f, full_name: e.target.value })} /></label>}
      <label>Email<input value={f.email} onChange={e => setF({ ...f, email: e.target.value })} /></label>
      <label>Mật khẩu<input type="password" value={f.password} onChange={e => setF({ ...f, password: e.target.value })} /></label>
      {err && <p className="err">{err}</p>}
      <button className="btn" disabled={busy}>{busy ? "Đang xử lý…" : reg ? "Đăng ký" : "Đăng nhập"}</button>
      <p className="muted">{reg ? <>Đã có tài khoản? <Link to="/login">Đăng nhập</Link></> : <>Chưa có tài khoản? <Link to="/register">Đăng ký</Link></>}</p>
    </form></div>);
}
