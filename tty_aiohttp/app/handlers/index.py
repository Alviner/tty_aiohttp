import logging

from aiohttp import web
from aiohttp.web_response import StreamResponse

from tty_aiohttp.app import TEMPLATE_ROOT

log = logging.getLogger(__name__)


class IndexHandler(web.View):
    async def get(self) -> StreamResponse:
        index_file = TEMPLATE_ROOT / "index.html"
        if not index_file.is_file():
            raise web.HTTPNotFound
        return web.FileResponse(index_file)
