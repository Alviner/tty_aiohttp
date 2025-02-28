import { Terminal, FitAddon, WebglAddon } from "vendor";

export default {
  data() {
    const fit = new FitAddon();
    const webgl = new WebglAddon();
    const term = new Terminal({
      cursorBlink: true,
      macOptionIsMeta: true,
      scrollback: true,
    });
    term.loadAddon(fit);
    term.loadAddon(webgl);

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

    this.$wsrpc.addRoute("pty.output", ({ data }) => {
      this.term.write(data);
    });
    await this.ready();

    this.$wsrpc.addEventListener("onconnect", this.ready);

    window.addEventListener("resize", this.fitToscreen);
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.fitToscreen);
    this.$wsrpc.removeEventListener("onconnect", this.ready);
  },
  methods: {
    async fitToscreen() {
      this.fit.fit();
      const dims = { width: this.term.cols, height: this.term.rows };
      await this.$wsrpc.proxy.pty.resize(dims);
    },
    async ready() {
      this.fit.fit();
      const dims = { width: this.term.cols, height: this.term.rows };
      await this.$wsrpc.proxy.pty.ready(dims);
    },
  },
  template: "<div style='width: 100vw; height: 100vh' ref='terminal'></div>",
};
