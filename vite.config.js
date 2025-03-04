import { defineConfig } from "vite";
import { compression } from "vite-plugin-compression2";
import vue from "@vitejs/plugin-vue";

// https://vite.dev/config/
const staticPath = "../tty_aiohttp/app/static";
export default defineConfig({
  root: "./frontend",
  build: {
    outDir: staticPath,
    emptyOutDir: true,
    sourcemap: true,
  },
  plugins: [
    vue(),
    compression({
      include: /\.(js|css|map|json|ico|eot|otf|ttf|woff|woff2)$/,
      deleteOriginalAssets: true,
    }),
  ],
});
