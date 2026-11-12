import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// /api -> FastAPI (đổi cổng nếu back-end chạy cổng khác)
export default defineConfig({ plugins: [react()], server: { proxy: { "/api": { target: "http://localhost:8000", rewrite: p => p.replace(/^\/api/, "") } } } });
