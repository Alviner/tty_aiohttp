import logging

from aiohttp import WSMessage
from wsrpc_aiohttp import WebSocketAsync

from tty_aiohttp.app.handlers.ws.pty import PtyHandler

log = logging.getLogger(__name__)


class PtyWebSocket(WebSocketAsync):
    async def handle_binary(self, message: WSMessage) -> None:
        route = self._handlers.get("pty")
        if not isinstance(route, PtyHandler):
            log.warning("Binary frame received but no PTY handler")
            return
        terminal = await route.terminal
        await terminal.write(message.data)
