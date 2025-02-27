import "element-plus/dist/index.css";
import WSRPC from "@wsrpc/client";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebglAddon } from "@xterm/addon-webgl";
import "@xterm/xterm/css/xterm.css";

import { createApp } from "vue/dist/vue.esm-bundler.js";

import elementPlusLocale from "element-plus/es/locale/lang/en.mjs";
import elementPlus, {
  ElLoading as Loading,
  ElMessage as Message,
  ElNotification as Notification,
} from "element-plus";

export {
  WSRPC,
  Terminal,
  FitAddon,
  WebglAddon,
  createApp,
  elementPlus,
  elementPlusLocale,
  Loading,
  Message,
  Notification,
};
