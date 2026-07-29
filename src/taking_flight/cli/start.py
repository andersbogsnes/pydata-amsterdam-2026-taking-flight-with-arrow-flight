from cyclopts import App

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

    from pyiceberg.catalog.rest import RestCatalog

    from taking_flight.flight_server.auth import TokenServerAuthHandler
    from taking_flight.flight_server.server import Server
    from taking_flight.settings import Settings

    settings = Settings()

    catalog = RestCatalog(
        "default",
        uri=settings.catalog_url,
        warehouse="default",
    )
    auth = TokenServerAuthHandler(token="pydataamsterdam")

    flight_server = Server(
        catalog=catalog, location=settings.flight_server_url, auth_handler=auth
    )

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

    app.console.print(f"Serving at {settings.flight_server_url}")
    flight_server.serve()
