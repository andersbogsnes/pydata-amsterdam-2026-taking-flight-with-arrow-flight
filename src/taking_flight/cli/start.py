import logging
import sys

from cyclopts import App

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", stream=sys.stdout)

app = App("start", help="Start the specified application")


@app.command()
def rest():
    import uvicorn

    from taking_flight.rest.app import app as rest_app

    uvicorn.run(rest_app, host="0.0.0.0", port=8000)


@app.command()
def server():
    import signal
    import threading

    from pyarrow.fs import S3FileSystem
    from pyiceberg.catalog.rest import RestCatalog

    from taking_flight.flight_server.repo import DatasetRepo
    from taking_flight.flight_server.server import Server
    from taking_flight.flight_server.settings import Settings
    from taking_flight.flight_server.auth import TokenServerAuthHandler

    settings = Settings()
    endpoint_url = (
        settings.s3_endpoint.unicode_string() if settings.s3_endpoint else None
    )
    s3fs = S3FileSystem(
        access_key=settings.access_key.get_secret_value(),
        secret_key=settings.secret_key.get_secret_value(),
        endpoint_override=endpoint_url,
        region=settings.region,
    )
    repo = DatasetRepo.from_url(settings.db_url.unicode_string())
    catalog = RestCatalog("default", **{
        "uri": settings.catalog_url,
        "warehouse": "default",
    })
    auth = TokenServerAuthHandler(token="copenhagendataengineering")

    flight_server = Server(s3fs, catalog=catalog, location=settings.location, dataset_repo=repo, auth_handler=auth)

    is_shutting_down = False

    # According to the docs, shutdown should happen in a separate thread.
    def shutdown_server(signum: int, _frame) -> None:
        nonlocal is_shutting_down
        if is_shutting_down:
            return
        is_shutting_down = True
        signal_name = signal.Signals(signum).name
        app.console.print(f"Received {signal_name}; shutting down")
        threading.Thread(target=flight_server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, shutdown_server)
    signal.signal(signal.SIGTERM, shutdown_server)

    app.console.print(f"Serving at {settings.location}")
    flight_server.serve()
