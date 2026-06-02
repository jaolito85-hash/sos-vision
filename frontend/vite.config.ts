import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Em produção a Sala é servida em /sala (a landing fica em /). No dev fica em /.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/sala/" : "/",
  plugins: [react()],
  server: { port: 5173 },
}));
