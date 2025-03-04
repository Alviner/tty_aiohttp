import "element-plus/dist/index.css";

import { createApp } from "vue";
import "./style.css";
import App from "./App.vue";
import locale from "element-plus/es/locale/lang/en.mjs";
import elementPlus from "element-plus";

import wsrpc from "./ws.js";

const app = createApp(App);
app.config.globalProperties.$wsrpc = wsrpc;
app.config.globalProperties.$json = (any) => JSON.stringify(any, null, 2);
app.use(elementPlus, { locale });

app.mount("#app");
export default app;
