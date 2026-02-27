import logging

from aiohttp import WSMessage
from wsrpc_aiohttp import WebSocketAsync

from tty_aiohttp.app.handlers.ws.pty import PtyHandler

log = logging.getLogger(__name__)

CMD_INPUT = 0x00
CMD_RESIZE = 0x01


class PtyWebSocket(WebSocketAsync):
    async def handle_binary(self, message: WSMessage) -> None:
        route = self._handlers.get("pty")
        if not isinstance(route, PtyHandler):
            log.warning("Binary frame received but no PTY handler")
            return

        data: bytes = message.data
        if not data:
            return

        cmd = data[0]
        payload = data[1:]

        if cmd == CMD_INPUT:
            terminal = await route.terminal
            await terminal.write(payload)
        elif cmd == CMD_RESIZE:
            if len(payload) == 4:
                rows = int.from_bytes(payload[0:2], "big")
                cols = int.from_bytes(payload[2:4], "big")
                terminal = await route.terminal
                terminal.resize(rows=rows, cols=cols)
