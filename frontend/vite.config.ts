import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 개발 시 /api 는 백엔드로 프록시한다. 프로덕션에서는 nginx 가 담당.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
