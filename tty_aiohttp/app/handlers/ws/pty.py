import asyncio
import fcntl
import os
import pty
import struct
import termios
import typing as t
from asyncio.subprocess import Process
from dataclasses import dataclass, field
from logging import getLogger

from aiohttp import web
from aiomisc.thread_pool import threaded
from wsrpc_aiohttp import Route, WSRPCBase, decorators
from wsrpc_aiohttp.websocket.abc import ProxyMethod

log = getLogger(__name__)

SHELL_KEY: web.AppKey[str] = web.AppKey("shell")


@dataclass
class PTYConfig:
    master_fd: int
    slave_fd: int
    shell: str

    @classmethod
    @threaded
    def open_pty(cls, shell: str) -> "PTYConfig":
        master_fd, slave_fd = pty.openpty()
        return cls(master_fd, slave_fd, shell)


@dataclass
class Terminal:
    process: Process
    fd: int
    proxy: ProxyMethod
    ws: web.WebSocketResponse

    _read_queue: asyncio.Queue[bytes] = field(
        init=False, default_factory=asyncio.Queue,
    )
    _write_queue: asyncio.Queue[bytes] = field(
        init=False, default_factory=asyncio.Queue,
    )
    _read_task: asyncio.Task[None] = field(init=False)
    _write_task: asyncio.Task[None] = field(init=False)
    _monitor_task: asyncio.Task[None] = field(init=False)

    def __post_init__(self) -> None:
        self._write_task = asyncio.create_task(self._write())
        self._read_task = asyncio.create_task(self._read())
        self._monitor_task = asyncio.create_task(self._monitor())
        asyncio.get_running_loop().add_reader(self.fd, self._on_read)

    async def _read(self) -> None:
        try:
            while True:
                chunk = await self._read_queue.get()
                await self.ws.send_bytes(chunk)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Error in terminal read task")

    async def write(self, chunk: bytes) -> None:
        await self._write_queue.put(chunk)

    async def _write(self) -> None:
        try:
            while True:
                chunk = await self._write_queue.get()
                await self._do_write(chunk)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Error in terminal write task")

    @threaded
    def _do_write(self, chunk: bytes) -> None:
        os.write(self.fd, chunk)

    def _on_read(self) -> None:
        try:
            data = os.read(self.fd, 1024 * 20)
            if not data:
                return
            self._read_queue.put_nowait(data)
        except OSError:
            return

    def resize(self, rows: int, cols: int) -> None:
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)

    async def _monitor(self) -> None:
        return_code = await self.process.wait()
        log.info("Process finished with return code %s", return_code)
        await self._close()

    async def _close(self) -> None:
        asyncio.get_running_loop().remove_reader(self.fd)
        self._read_task.cancel()
        self._write_task.cancel()
        os.close(self.fd)
        message = (
            f"Shell was closed\n"
            f"with return code {self.process.returncode}"
        )
        try:
            await self.proxy.notify(
                type="error",
                title="Terminal is closed",
                message=message,
            )
        except ConnectionError:
            log.debug("Could not send close notification, connection lost")

    async def close(self) -> None:
        if self.process.returncode is not None:
            log.info(
                "Process already closed with return code %s",
                self.process.returncode,
            )
            return
        self.process.kill()
        await self.process.wait()


class PtyHandler(Route):
    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._terminal: Terminal | None = None
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def shell(self) -> str:
        return self.socket.request.app[SHELL_KEY]

    @property
    async def terminal(self) -> Terminal:
        async with self._lock:
            if self._terminal is not None:
                return self._terminal

            pty_config = await PTYConfig.open_pty(self.shell)
            socket: WSRPCBase = self.socket  # type: ignore

            process = await asyncio.create_subprocess_exec(
                self.shell,
                preexec_fn=os.setsid,
                stdin=pty_config.slave_fd,
                stdout=pty_config.slave_fd,
                stderr=pty_config.slave_fd,
                env=os.environ.copy(),
                close_fds=True,
            )
            os.close(pty_config.slave_fd)

            self._terminal = Terminal(
                process,
                pty_config.master_fd,
                socket.proxy.pty,
                socket.socket,  # type: ignore[attr-defined]
            )
            return self._terminal

    @decorators.proxy
    async def ready(self, cols: int, rows: int) -> None:
        await self.resize(cols=cols, rows=rows)

    @decorators.proxy
    async def resize(self, rows: int, cols: int) -> None:
        terminal = await self.terminal
        terminal.resize(rows=rows, cols=cols)

    def _onclose(self) -> t.Any:  # type: ignore
        log.info("Closing terminal")
        terminal, self._terminal = self._terminal, None
        if terminal is None:
            return
        return terminal.close()
