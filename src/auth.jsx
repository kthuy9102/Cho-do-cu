import { createContext, useContext, useState } from "react";
import { Navigate } from "react-router-dom";
const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("user") || "null"));
  const login = (token, u) => { localStorage.setItem("token", token); localStorage.setItem("user", JSON.stringify(u)); setUser(u); };
  const logout = () => { localStorage.clear(); setUser(null); };
  return <Ctx.Provider value={{ user, login, logout }}>{children}</Ctx.Provider>;
}
export function Guard({ role, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (role && user.role !== role) return <div className="wrap"><h2>403 – Bạn không có quyền vào trang này</h2></div>;
  return children;
}
