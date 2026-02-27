import WSRPC from "@wsrpc/client";

import { ElLoading as Loading } from "element-plus";
import 'element-plus/es/components/loading/style/css'

let _binaryHandler = null;

const OriginalWebSocket = window.WebSocket;

window.WebSocket = function(url, protocols) {
    const ws = new OriginalWebSocket(url, protocols);
    ws.binaryType = "arraybuffer";

    let _wsrpcOnMessage = null;

    Object.defineProperty(ws, "onmessage", {
        get() {
            return _wsrpcOnMessage;
        },
        set(handler) {
            _wsrpcOnMessage = handler;
        },
    });

    ws.addEventListener("message", function(event) {
        if (event.data instanceof ArrayBuffer) {
            if (_binaryHandler) {
                _binaryHandler(event.data);
            }
        } else if (_wsrpcOnMessage) {
            _wsrpcOnMessage(event);
        }
    });

    return ws;
};
window.WebSocket.CONNECTING = OriginalWebSocket.CONNECTING;
window.WebSocket.OPEN = OriginalWebSocket.OPEN;
window.WebSocket.CLOSING = OriginalWebSocket.CLOSING;
window.WebSocket.CLOSED = OriginalWebSocket.CLOSED;
window.WebSocket.prototype = OriginalWebSocket.prototype;

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

export function setBinaryHandler(callback) {
    _binaryHandler = callback;
}

export default wsrpc;
