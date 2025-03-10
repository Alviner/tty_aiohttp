import logging
import os
from socket import socket
from sys import argv

import configargparse
import forklib
from aiomisc import Service, bind_socket, entrypoint
from aiomisc.log import basic_config
from aiomisc.service.raven import RavenSender
from setproctitle import setproctitle

from tty_aiohttp import __version__
from tty_aiohttp.app.arguments import parser
from tty_aiohttp.app.services.rest import REST
from tty_aiohttp.app.utils.serializers import config_serializers
from tty_aiohttp.utils.http.filters import config_filters

log = logging.getLogger(__name__)


def _run_worker(
    name: str,
    args: configargparse.Namespace,
    rest_sock: socket,
) -> None:
    log.info("Worker with PID %s started", os.getpid())
    setproctitle(f"[Worker] {name}")
    services: list[Service] = [
        REST(
            sock=rest_sock,
            debug=args.debug,
            env=args.sentry_env,
            shell=args.shell,
        ),
    ]
    if args.sentry_dsn:
        services.append(
            RavenSender(
                sentry_dsn=args.sentry_dsn,
                client_options=dict(
                    name="app",
                    environment=args.sentry_env,
                    release=__version__,
                ),
            )
        )
    with entrypoint(
        *services,
        log_level=args.log_level,
        log_format=args.log_format,
        pool_size=args.pool_size,
        debug=args.debug,
    ) as loop:
        loop.run_forever()


def main() -> None:
    args = parser.parse_args()
    basic_config(
        level=args.log_level,
        log_format=args.log_format,
        buffered=False,
    )
    sock = bind_socket(
        address=args.api_address,
        port=args.api_port,
        proto_name="http",
    )
    if args.user is not None:
        logging.info("Changing user to %r", args.user.pw_name)
        os.setgid(args.user.pw_gid)
        os.setuid(args.user.pw_uid)
    app_name = os.path.basename(argv[0])

    config_serializers()
    config_filters()

    forklib.fork(
        args.forks,
        entrypoint=lambda: _run_worker(app_name, args, sock),
    )


if __name__ == "__main__":
    main()
