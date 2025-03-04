import { createApp } from "vue";
import "./style.css";
import App from "./App.vue";

import wsrpc from "./ws.js";

const app = createApp(App);
app.config.globalProperties.$wsrpc = wsrpc;
app.config.globalProperties.$json = (any) => JSON.stringify(any, null, 2);

app.mount("#app");
export default app;
