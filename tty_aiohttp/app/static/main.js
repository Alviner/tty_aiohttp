import { createApp, elementPlus, elementPlusLocale as locale } from "vendor";

import App from "./App.js";
import wsrpc from "./api/ws.js";

const app = createApp({
  ...App,
  beforeCreate: function () {
    wsrpc.connect();
  },
});

app.config.globalProperties.$wsrpc = wsrpc;
app.config.globalProperties.$json = (any) => JSON.stringify(any, null, 2);

app.use(elementPlus, { locale }).mount("#app");

export default app;
