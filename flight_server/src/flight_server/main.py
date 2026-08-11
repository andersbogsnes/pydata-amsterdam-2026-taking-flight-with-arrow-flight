import signal
import threading

import structlog

from flight_server import logging
from flight_server.auth import TokenServerAuthHandler
from flight_server.server import Server
from flight_server.settings import Settings


def run_server() -> None:
    settings = Settings()
    logging.configure_logging(settings.mode == "local")

    logger = structlog.get_logger(__name__)

    flight_server = Server(
        settings,
        location=settings.flight_server_url,
        auth_handler=None if settings.mode == "local" else TokenServerAuthHandler(token=settings.token),
    )

    is_shutting_down = False

    # According to the docs, shutdown should happen in a separate thread.
    def shutdown_server(signum: int, _frame) -> None:
        nonlocal is_shutting_down
        if is_shutting_down:
            return
        is_shutting_down = True
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}; shutting down")
        threading.Thread(target=flight_server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, shutdown_server)
    signal.signal(signal.SIGTERM, shutdown_server)

    logger.info(f"Serving at {settings.flight_server_url}")
    flight_server.serve()


if __name__ == "__main__":
    run_server()
