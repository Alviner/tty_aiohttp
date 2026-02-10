# tty_aiohttp

Web-based terminal (TTY) emulator. Provides interactive shell access through a browser using WebSocket RPC and xterm.js.

## Architecture

- **Backend**: Python 3.12+ async web server on aiohttp + aiomisc with multi-process workers (forklib)
- **Frontend**: Vue.js 3 + xterm.js terminal emulator
- **Protocol**: WebSocket RPC (wsrpc-aiohttp) for bidirectional communication
- **Shell**: Spawns a configurable shell process (default `/usr/bin/zsh`) with PTY support

## Requirements

- Python >= 3.12
- Node.js + Yarn (for frontend build)
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Development

```bash
# Setup environment (python + node dependencies)
make develop

# Run locally
uv run tty_aiohttp

# Run tests
make pytest

# Type checking + linting (mypy, ruff)
make lint

# Code formatting
make format
```

## Make targets

| Command        | Description                             |
| -------------- | --------------------------------------- |
| `make develop` | Create virtualenv, install dependencies |
| `make pytest`  | Run pytest                              |
| `make lint`    | Run mypy and ruff                       |
| `make format`  | Format code with ruff                   |
| `make static`  | Build frontend (Vite)                   |
| `make wheel`   | Build Python wheel                      |
| `make build`   | Build Docker image                      |
| `make upload`  | Push Docker image to registry           |
| `make clean`   | Remove dist directory                   |
| `make purge`   | Remove dist and .venv                   |

## Configuration

Arguments are parsed via `configargparse` with the `APP_` environment variable prefix.

| Argument          | Env variable      | Default        | Description                   |
| ----------------- | ----------------- | -------------- | ----------------------------- |
| `--api-address`   | `APP_API_ADDRESS` | `127.0.0.1`    | Bind address                  |
| `--api-port`      | `APP_API_PORT`    | `9090`         | Listen port                   |
| `--shell`         | `APP_SHELL`       | `/usr/bin/zsh` | Shell executable              |
| `--forks`         | `APP_FORKS`       | `4`            | Number of worker processes    |
| `-s, --pool-size` | `APP_POOL_SIZE`   | `4`            | Thread pool size              |
| `-D, --debug`     | `APP_DEBUG`       | `false`        | Enable debug mode             |
| `--log-level`     | `APP_LOG_LEVEL`   | `info`         | Log verbosity                 |
| `--log-format`    | `APP_LOG_FORMAT`  | `color`        | Log format                    |
| `--sentry-dsn`    | `APP_SENTRY_DSN`  |                | Sentry DSN for error tracking |
| `-u, --user`      | `APP_USER`        |                | Change process UID            |

Config file locations (auto-loaded):

- `~/.config/tty_aiohttp/app.conf`
- `/etc/tty_aiohttp/app.conf`

## API Endpoints

| Method | Path           | Description                  |
| ------ | -------------- | ---------------------------- |
| GET    | `/`            | Web terminal UI (index.html) |
| GET    | `/icon.svg`    | Application icon             |
| GET    | `/api/v1/ping` | Health check                 |
| GET    | `/assets/*`    | Static frontend assets       |
| WS     | `/ws/`         | WebSocket RPC (terminal I/O) |

## Docker

```bash
# Build image
make build

# Push to registry
make upload
```

The Docker image is based on `snakepacker/python:3.13` and includes zsh, git, vim, neovim, curl, htop, and oh-my-zsh.

Environment variable `APP_API_ADDRESS` is set to `0.0.0.0` in the container.
