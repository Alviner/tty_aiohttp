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
    slave_fd: int
    read_queue: asyncio.Queue[str]
    write_queue: asyncio.Queue[str]
    proxy: ProxyMethod

    _read_task: asyncio.Task[None] = field(init=False)
    _write_task: asyncio.Task[None] = field(init=False)
    _monitor_task: asyncio.Task[None] = field(init=False)

    def __post_init__(self) -> None:
        """Initialize terminal tasks"""
        self._write_task = asyncio.create_task(self._write())
        self._read_task = asyncio.create_task(self._read())
        self._monitor_task = asyncio.create_task(self._monitor())
        loop = asyncio.get_event_loop()
        loop.add_reader(self.fd, self.on_read)

    async def _read(self) -> None:
        while True:
            chunk = await self.read_queue.get()
            await self.proxy.output(data=chunk)

    async def write(self, chunk: str) -> None:
        await self.write_queue.put(chunk)

    async def _write(self) -> None:
        while True:
            chunk = await self.write_queue.get()
            await self._do_write(chunk.encode("utf-8"))

    @threaded
    def _do_write(self, chunk: bytes) -> None:
        os.write(self.fd, chunk)

    @threaded
    def _do_close(self, fd: int) -> None:
        os.close(fd)

    def on_read(self) -> None:
        max_read_bytes = 1024 * 20
        output = os.read(self.fd, max_read_bytes).decode(errors="ignore")
        self.read_queue.put_nowait(output)

    @threaded
    def resize(
        self,
        rows: int,
        cols: int,
        xpix: int = 0,
        ypix: int = 0,
    ) -> None:
        winsize = struct.pack("HHHH", rows, cols, xpix, ypix)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)

    async def _monitor(self) -> None:
        return_code = await self.process.wait()
        log.info("Process was finished with return code %s", return_code)
        await self._close()

    async def _close(self) -> None:
        loop = asyncio.get_event_loop()
        loop.remove_reader(self.fd)
        self._read_task.cancel()
        self._write_task.cancel()
        await self._do_close(self.fd)
        await self._do_close(self.slave_fd)
        message = f"""Shell was closed
with return code {self.process.returncode}"""
        await self.proxy.notify(
            type="error",
            title="Terminal is closed",
            message=message,
        )

    async def close(self) -> None:
        if (return_code := self.process.returncode) is not None:
            log.info(
                "Process was already closed with return code %s",
                return_code,
            )
            return
        self.process.kill()


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
            self._terminal = Terminal(
                process,
                pty_config.master_fd,
                pty_config.slave_fd,
                asyncio.Queue(),
                asyncio.Queue(),
                socket.proxy.pty,
            )
            return self._terminal

    @decorators.proxy
    async def ready(self, cols: int, rows: int) -> None:
        await self.resize(cols=cols, rows=rows)

    @decorators.proxy
    async def input(self, data: str) -> None:
        terminal = await self.terminal
        await terminal.write(data)

    @decorators.proxy
    async def resize(self, rows: int, cols: int) -> None:
        terminal = await self.terminal
        await terminal.resize(rows=rows, cols=cols)

    def _onclose(self) -> t.Any:  # type: ignore
        log.info("Closing terminal")
        terminal = self._terminal
        self._terminal = None
        if terminal is None:
            return
        return terminal.close()
