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

log = getLogger(__name__)

SHELL_KEY: web.AppKey[str] = web.AppKey("shell")
TERMINALS_KEY: web.AppKey[set["Terminal"]] = web.AppKey("terminals")


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


@dataclass(eq=False)
class Terminal:
    process: Process
    fd: int
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
    _closed: bool = field(init=False, default=False)

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
        self._cleanup_io()
        message = (
            "\r\n\x1b[31m"
            f"Process closed with code {return_code}"
            "\x1b[0m\r\n"
        )
        try:
            await self.ws.send_bytes(message.encode())
        except (ConnectionError, asyncio.CancelledError):
            log.debug(
                "Could not send close notification, connection lost",
            )

    def _cleanup_io(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            asyncio.get_running_loop().remove_reader(self.fd)
        except (ValueError, OSError):
            pass
        self._read_task.cancel()
        self._write_task.cancel()
        try:
            os.close(self.fd)
        except OSError:
            pass

    async def close(self) -> None:
        self._monitor_task.cancel()
        self._cleanup_io()
        if self.process.returncode is None:
            self.process.kill()
            try:
                await asyncio.wait_for(
                    self.process.wait(), timeout=5.0,
                )
            except TimeoutError:
                log.warning(
                    "Process %s did not exit after kill",
                    self.process.pid,
                )


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

            env = os.environ.copy()
            env["TERM"] = "xterm-256color"
            env["COLORTERM"] = "truecolor"

            process = await asyncio.create_subprocess_exec(
                self.shell,
                preexec_fn=os.setsid,
                stdin=pty_config.slave_fd,
                stdout=pty_config.slave_fd,
                stderr=pty_config.slave_fd,
                env=env,
                close_fds=True,
            )
            os.close(pty_config.slave_fd)

            self._terminal = Terminal(
                process,
                pty_config.master_fd,
                socket.socket,  # type: ignore[attr-defined]
            )
            app = self.socket.request.app
            app[TERMINALS_KEY].add(self._terminal)
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
        app = self.socket.request.app
        return _close_and_untrack(terminal, app)


async def _close_and_untrack(
    terminal: Terminal, app: web.Application,
) -> None:
    try:
        await terminal.close()
    finally:
        app[TERMINALS_KEY].discard(terminal)


async def close_all_terminals(app: web.Application) -> None:
    terminals: set[Terminal] = app[TERMINALS_KEY]
    to_close = list(terminals)
    terminals.clear()
    for terminal in to_close:
        try:
            await terminal.close()
        except Exception:
            log.exception("Error closing terminal on shutdown")
