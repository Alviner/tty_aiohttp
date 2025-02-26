from tty_aiohttp.app.handlers.ws.env import EnvModel


async def test_ws_awesome(wsrpc_client):
    resp = await wsrpc_client.call("env.load")
    EnvModel.parse_obj(resp)
    assert "environment" in resp
