from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

import fast_json
from aiohttp import web


class BaseHandler(web.View):

    def json_response(
        self, data: Any, headers: Mapping[str, str], status: HTTPStatus
    ) -> web.Response:
        return web.Response(
            body=fast_json.dumps(data),
            content_type="application/json",
            status=status,
            headers=(headers or {}),
        )
