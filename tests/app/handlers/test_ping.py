from http import HTTPStatus

from tty_aiohttp import __version__
from tty_aiohttp.app.handlers.v1.ping import X_VERSION

URL = "/api/v1/ping"


async def test_version(api_client):
    resp = await api_client.get(URL)
    assert resp.status == HTTPStatus.OK
    assert resp.headers[X_VERSION] == __version__
