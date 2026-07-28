import cyclopts
from python_on_whales import DockerClient

stop_app = cyclopts.App(name="stop")


def _stop_compose(services: list[str] | None, remove_volumes: bool = True) -> None:
    docker = DockerClient()
    docker.compose.down(
        services=services, quiet=True, remove_orphans=True, volumes=remove_volumes, timeout=10
    )


@stop_app.command()
def rest() -> None:
    """Stop the rest service."""
    _stop_compose(services=["rest"])


@stop_app.command()
def server() -> None:
    """Stop the Arrow Flight server."""
    _stop_compose(services=["server"])


@stop_app.command()
def notebook() -> None:
    """Stop JupyterLab server"""
    _stop_compose(services=["notebook"])


@stop_app.command()
def db() -> None:
    """Stop the database."""
    _stop_compose(services=["db"])


@stop_app.command()
def storage() -> None:
    """Start the fs."""
    _stop_compose(services=["storage"])
