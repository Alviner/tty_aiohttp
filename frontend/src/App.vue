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

        const CMD_INPUT = 0x00;
        const CMD_RESIZE = 0x01;
        const encoder = new TextEncoder();

        this.term.onData((data) => {
            const encoded = encoder.encode(data);
            const msg = new Uint8Array(1 + encoded.length);
            msg[0] = CMD_INPUT;
            msg.set(encoded, 1);
            this.$wsrpc.sendRaw(msg);
        });
        this.term.onBinary((data) => {
            const raw = Uint8Array.from(data, (c) => c.charCodeAt(0));
            const msg = new Uint8Array(1 + raw.length);
            msg[0] = CMD_INPUT;
            msg.set(raw, 1);
            this.$wsrpc.sendRaw(msg);
        });
        this.term.onResize(({ cols, rows }) => {
            const msg = new Uint8Array(5);
            const view = new DataView(msg.buffer);
            msg[0] = CMD_RESIZE;
            view.setUint16(1, rows);
            view.setUint16(3, cols);
            this.$wsrpc.sendRaw(msg);
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
            if (!this._resizeRaf) {
                this._resizeRaf = requestAnimationFrame(() => {
                    this._resizeRaf = null;
                    this.fit.fit();
                });
            }
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
