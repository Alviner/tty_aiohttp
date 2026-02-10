import json
import logging
from http import HTTPStatus

from aiohttp import web, web_exceptions
from aiomisc import timeout

from tty_aiohttp import __version__
from tty_aiohttp.app.handlers import BaseHandler

X_VERSION = "X-VERSION"


log = logging.getLogger(__name__)


class PingHandler(BaseHandler):
    @timeout(5)
    async def get(self) -> web.Response:
        status = True

        status_code = HTTPStatus.OK
        if not status:
            raise web_exceptions.HTTPInternalServerError

        return web.json_response(
            data={"status": status},
            status=status_code,
            headers={X_VERSION: __version__},
            dumps=json.dumps,
        )
