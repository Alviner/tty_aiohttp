try:
    from importlib.metadata import Distribution

    __version__ = Distribution.from_name("tty_aiohttp").version
except ImportError:
    __version__ = "0.0.0"
