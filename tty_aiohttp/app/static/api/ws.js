import { Loading, WSRPC } from "vendor";

const wsrpc = new WSRPC("/ws/");
let loading;

wsrpc.addEventListener("onconnect", function () {
  console.log("Connection established");
  if (loading) {
    loading.close();
    loading = undefined;
  }
});

wsrpc.addEventListener("onerror", function () {
  console.error("Connection lost");
  loading = Loading.service({
    lock: true,
    text: "Connection is lost",
    spinner: "el-icon-loading",
    background: "rgba(0, 0, 0, 0.7)",
  });
});

export default wsrpc;
