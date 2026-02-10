import logging
from itertools import chain
from typing import Any

from aiohttp import web
from aiohttp.web_app import Application, Middleware
from aiomisc.service.aiohttp import AIOHTTPService
from wsrpc_aiohttp import WebSocketAsync

from tty_aiohttp.app import ASSETS_ROOT, FONTS_ROOT
from tty_aiohttp.app.handlers.index import IconHandler, IndexHandler
from tty_aiohttp.app.handlers.static import StaticResource
from tty_aiohttp.app.handlers.v1.ping import PingHandler
from tty_aiohttp.app.handlers.ws.pty import SHELL_KEY, PtyHandler
from tty_aiohttp.app.utils.serializers import config_serializers
from tty_aiohttp.utils.argparse import Environment

log = logging.getLogger(__name__)

DEFAULT_SHELL = "/usr/bin/zsh"

ApiHandlersType = tuple[tuple[str, str, Any], ...]
WsHandlersType = tuple[tuple[str, Any], ...]


class REST(AIOHTTPService):
    __required__ = ("env",)

    env: Environment
    shell: str = DEFAULT_SHELL

    _middlewares: tuple[Middleware, ...] = tuple()
    __dependencies__: tuple[str, ...] = tuple()

    API_ROUTES: ApiHandlersType = (
        ("GET", "/", IndexHandler),
        ("GET", "/icon.svg", IconHandler),
        ("GET", "/api/v1/ping", PingHandler),
    )

    WS_ROUTES: WsHandlersType = (("pty", PtyHandler),)

    async def create_application(self) -> Application:
        config_serializers()
        app = web.Application()

        self._add_routes(app)
        self._add_middlewares(app)
        self._set_dependencies(app)
        return app

    def _add_routes(self, app: Application) -> None:
        for method, path, handler in self.API_ROUTES:
            app.router.add_route(
                method=method,
                path=path,
                handler=handler,
            )
        app.router.add_route("*", "/ws/", WebSocketAsync)
        for route, handler in self.WS_ROUTES:
            WebSocketAsync.add_route(
                route=route,
                handler=handler,
            )

        app.router.register_resource(StaticResource("/assets", ASSETS_ROOT))
        app.router.register_resource(StaticResource("/fonts", FONTS_ROOT))

    def _set_dependencies(self, app: Application) -> None:
        for name in chain(self.__required__, self.__dependencies__):
            app[name] = getattr(self, name)
        app[SHELL_KEY] = self.shell

    def _add_middlewares(self, app: web.Application) -> None:
        for middleware in self._middlewares:
            app.middlewares.append(middleware)
