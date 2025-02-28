import {
  Terminal,
  FitAddon,
  WebglAddon,
  ClipboardAddon,
  WebLinksAddon,
  Notification,
} from "vendor";

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

    this.$wsrpc.addEventListener("onconnect", this.ready);
    this.$wsrpc.addRoute("pty.notify", this.notify);
    this.$wsrpc.addRoute("pty.output", this.output);
    window.addEventListener("resize", this.fitToscreen);
    await this.ready();
    this.term.focus();
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.fitToscreen);
    this.$wsrpc.removeRoute("pty.output", this.output);
    this.$wsrpc.removeRoute("pty.notify", this.notify);
    this.$wsrpc.removeEventListener("onconnect", this.ready);
  },
  methods: {
    async fitToscreen() {
      this.fit.fit();
      const dims = { width: this.term.cols, height: this.term.rows };
      await this.$wsrpc.proxy.pty.resize(dims);
    },
    output({ data }) {
      this.term.write(data);
    },
    async ready() {
      this.fit.fit();
      const dims = { width: this.term.cols, height: this.term.rows };
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
  template: "<div style='width: 100vw; height: 100vh' ref='terminal'></div>",
};
