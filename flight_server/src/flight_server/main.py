import signal
import threading

import structlog
from pyiceberg.catalog.rest import RestCatalog
from pyiceberg.exceptions import RESTError

from flight_server import logging
from flight_server.auth import TokenServerAuthHandler
from flight_server.exceptions import IcebergCatalogueException
from flight_server.server import Server
from flight_server.settings import Settings

logging.configure_logging()


def run_server() -> None:
    logger = structlog.get_logger(__name__)
    settings = Settings()

    try:
        catalog = RestCatalog(
            "default",
            uri=settings.catalog_url,
            warehouse=settings.warehouse,
            **{"rest.sigv4-enabled": "true",
               "rest.signing-name": "s3tables",
               "rest.signing-region": "eu-north-1"},
        )
    except RESTError as e:
        raise IcebergCatalogueException("unable to connect to Iceberg Catalog") from e

    logger.info("connected to Iceberg catalog",
                catalog=settings.catalog_url,
                warehouse=settings.warehouse)

    flight_server = Server(
        catalog=catalog,
        location=settings.flight_server_url,
        auth_handler=TokenServerAuthHandler(token="pydataamsterdam")
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


if __name__ == '__main__':
    run_server()
