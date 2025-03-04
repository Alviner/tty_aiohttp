from http import HTTPStatus


async def test_index(api_client):
    async with api_client.get("/") as resp:
        assert resp.status == HTTPStatus.OK
        body = await resp.text()
        assert '<div id="app"' in body


async def test_icon(api_client):
    async with api_client.get("/icon.svg") as resp:
        assert resp.status == HTTPStatus.OK
        body = await resp.text()
        assert "<svg" in body


async def test_not_found_static_file(api_client):
    async with api_client.get("/another-page") as resp:
        assert resp.status == HTTPStatus.NOT_FOUND
