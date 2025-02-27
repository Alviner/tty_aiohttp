import "element-plus/dist/index.css";
import WSRPC from "@wsrpc/client";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebglAddon } from "@xterm/addon-webgl";
import "@xterm/xterm/css/xterm.css";

import { createApp } from "vue/dist/vue.esm-bundler.js";

import {
  createRouter,
  createWebHistory,
  RouterLink,
} from "vue-router/dist/vue-router.esm-bundler.js";

import elementPlusLocale from "element-plus/es/locale/lang/en.mjs";
import elementPlus, {
  ElLoading as Loading,
  ElMessage as Message,
  ElNotification as Notification,
} from "element-plus";

import { v4 as uuidv4 } from "uuid";

export {
  WSRPC,
  Terminal,
  FitAddon,
  WebglAddon,
  createApp,
  createWebHistory,
  createRouter,
  RouterLink,
  elementPlus,
  elementPlusLocale,
  Loading,
  Message,
  Notification,
  uuidv4,
};
