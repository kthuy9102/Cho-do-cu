import { Routes, Route, Link, useNavigate } from "react-router-dom";
import { useAuth, Guard } from "./auth.jsx";
import Home from "./pages/Home.jsx";
import Detail from "./pages/Detail.jsx";
import Auth from "./pages/Auth.jsx";
import Create from "./pages/Create.jsx";
import { Mine, Moderation } from "./pages/Manage.jsx";
export default function App() {
  const { user, logout } = useAuth(); const nav = useNavigate();
  return (<>
    <header className="bar"><Link to="/" className="logo">Chợ đồ cũ<b>SV</b></Link>
      <nav>
        {user ? <>
          <Link to="/create">Đăng tin</Link><Link to="/mine">Tin của tôi</Link>
          {user.role === "moderator" && <Link to="/moderation">Kiểm duyệt</Link>}
          <span className="who">{user.full_name}</span>
          <button className="ghost" onClick={() => { logout(); nav("/"); }}>Đăng xuất</button>
        </> : <><Link to="/login">Đăng nhập</Link><Link to="/register" className="btn sm">Đăng ký</Link></>}
      </nav></header>
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/listings/:id" element={<Detail />} />
      <Route path="/login" element={<Auth mode="login" />} />
      <Route path="/register" element={<Auth mode="register" />} />
      <Route path="/create" element={<Guard><Create /></Guard>} />
      <Route path="/mine" element={<Guard><Mine /></Guard>} />
      <Route path="/moderation" element={<Guard role="moderator"><Moderation /></Guard>} />
      <Route path="*" element={<div className="wrap"><h2>Không tìm thấy trang</h2></div>} />
    </Routes></>);
}
