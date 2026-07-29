import subprocess

from pyarrow.fs import FileSystem
from python_on_whales import DockerClient

from taking_flight.cli.console import console


def _start_compose() -> None:
    docker = DockerClient()
    docker.compose.up(
        detach=True,
        build=True,
    )


def _stop_compose(remove_volumes: bool = True) -> None:
    docker = DockerClient()
    docker.compose.down(remove_orphans=True, volumes=remove_volumes, timeout=10)


def _start_notebook():
    try:
        subprocess.run(["jupyter", "lab", "--notebook-dir", "notebooks"], check=True)
    except subprocess.CalledProcessError as e:
        console.print("Failed to start JupyterLab")
        console.print(e.output)
        raise


def _create_bucket(fs: FileSystem, bucket_name: str) -> None:
    fs.create_dir(bucket_name)
