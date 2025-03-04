import { defineConfig } from "vite";
import { compression } from "vite-plugin-compression2";
import vue from "@vitejs/plugin-vue";
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import ElementPlus from 'unplugin-element-plus/vite'

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
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
    ElementPlus(),
    compression({
      include: /\.(js|css|map|json|ico|eot|otf|ttf|woff|woff2)$/,
      deleteOriginalAssets: true,
    }),
  ],
});
