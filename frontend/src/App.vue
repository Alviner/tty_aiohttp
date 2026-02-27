<script>
import wsrpc, { setBinaryHandler } from "./ws.js";
import "@xterm/xterm/css/xterm.css";

import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { CanvasAddon } from "@xterm/addon-canvas";
import { ClipboardAddon } from "@xterm/addon-clipboard";
import { WebLinksAddon } from "@xterm/addon-web-links";
import { LigaturesAddon } from "@xterm/addon-ligatures";

export default {
    data() {
        const fit = new FitAddon();
        const canvas = new CanvasAddon();
        const clipboard = new ClipboardAddon();
        const links = new WebLinksAddon();
        const term = new Terminal({
            cursorBlink: true,
            macOptionIsMeta: true,
            scrollback: true,
            fontFamily: "'LigaHack Nerd Font', monospace",
            fontSize: 14,
            allowProposedApi: true,
        });
        term.loadAddon(fit);
        term.loadAddon(canvas);
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
        this.term.loadAddon(new LigaturesAddon());

        const encoder = new TextEncoder();
        this.term.onData((data) => {
            this.$wsrpc.sendRaw(encoder.encode(data));
        });
        this.term.onBinary((data) => {
            this.$wsrpc.sendRaw(Uint8Array.from(data, (c) => c.charCodeAt(0)));
        });
        this.term.onResize(({ cols, rows }) => {
            this.$wsrpc.proxy.pty.resize({ rows, cols });
        });

        this.$wsrpc.addEventListener("onconnect", this.ready);
        setBinaryHandler((buf) => this.term.write(new Uint8Array(buf)));

        this._resizeObserver = new ResizeObserver(() => this.fitToscreen());
        this._resizeObserver.observe(this.$refs.terminal);

        await this.ready();
        this.term.focus();
    },
    beforeUnmount() {
        this._resizeObserver?.disconnect();
        setBinaryHandler(null);
        this.$wsrpc.removeEventListener("onconnect", this.ready);
    },
    beforeCreate() {
        this.$wsrpc.connect();
    },
    methods: {
        fitToscreen() {
            clearTimeout(this._resizeTimer);
            this._resizeTimer = setTimeout(() => {
                requestAnimationFrame(() => this.fit.fit());
            }, 100);
        },
        async ready() {
            this.fit.fit();
            const dims = { cols: this.term.cols, rows: this.term.rows };
            await this.$wsrpc.proxy.pty.ready(dims);
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
    background-color: #000;
}
</style>
