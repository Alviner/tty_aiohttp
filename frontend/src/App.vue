<script>
import wsrpc from "./ws.js";
import { ElNotification as Notification } from "element-plus";
import 'element-plus/es/components/notification/style/css'
import "@xterm/xterm/css/xterm.css";

import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebglAddon } from "@xterm/addon-webgl";
import { ClipboardAddon } from "@xterm/addon-clipboard";
import { WebLinksAddon } from "@xterm/addon-web-links";

export default {
    data() {
        const fit = new FitAddon();
        const webgl = new WebglAddon();
        const clipboard = new ClipboardAddon();
        const links = new WebLinksAddon();

        const term = new Terminal({
            cursorBlink: true,
            macOptionIsMeta: true,
            scrollback: true,
            fontFamily: "'Hack Nerd Font Mono', monospace",
            fontSize: 14,
        });
        term.loadAddon(fit);
        term.loadAddon(webgl);
        term.loadAddon(clipboard);
        term.loadAddon(links);

        return {
            term,
            fit,
        };
    },
    computed: {},
    async mounted() {
        this.term.open(this.$refs.terminal);

        this.term.onData(async (data) => {
            await this.$wsrpc.proxy.pty.input({ data });
        });
        this.term.onResize(async ({ cols, rows }) => {
            console.log("resize term", cols, rows);
            await this.$wsrpc.proxy.pty.resize({ rows, cols });
        });

        this.$wsrpc.addEventListener("onconnect", this.ready);
        this.$wsrpc.addRoute("pty.notify", this.notify);
        this.$wsrpc.addRoute("pty.output", this.output);

        this._resizeObserver = new ResizeObserver(() => this.fitToscreen());
        this._resizeObserver.observe(this.$refs.terminal);

        await this.ready();
        this.term.focus();
    },
    beforeUnmount() {
        this._resizeObserver?.disconnect();
        this.$wsrpc.removeRoute("pty.output", this.output);
        this.$wsrpc.removeRoute("pty.notify", this.notify);
        this.$wsrpc.removeEventListener("onconnect", this.ready);
    },
    beforeCreate() {
        this.$wsrpc.connect();
    },
    methods: {
        fitToscreen() {
            clearTimeout(this._resizeTimer);
            this._resizeTimer = setTimeout(() => this.fit.fit(), 50);
        },
        output({ data }) {
            this.term.write(data);
        },
        async ready() {
            this.fit.fit();
            const dims = { cols: this.term.cols, rows: this.term.rows };
            await this.$wsrpc.proxy.pty.ready(dims);
        },
        async notify({ title, message, type }) {
            Notification({
                title,
                message,
                type,
            });
        },
    },
};
</script>

<template>
    <div class="terminal" ref="terminal"></div>
</template>

<style scoped>
.terminal {
    width: 100%;
    height: 100%;
}
</style>
