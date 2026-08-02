import pathlib
import tempfile

import cyclopts
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from fly.data.download import _download_zip_file, _fetch_expected_size, _unzip_file

cmd = cyclopts.App(name="data", help="manage data")

DATA_DIR = pathlib.Path(__file__).parents[3] / "data"
DATA_URL = "https://s3.amazonaws.com/tripdata"
DEFAULT_DATA_URL = "https://s3.amazonaws.com/tripdata/202601-citibike-tripdata.zip"


@cmd.command
def download(output_folder: pathlib.Path = DATA_DIR, year: int = 2026, month: int = 1):
    """Download City Bike data"""
    download_progress = Progress(
        "{task.description}",
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )
    unzip_progress = Progress(
        SpinnerColumn(finished_text="[green]✔[/green]"),
        "{task.description}",
    )
    file_name = f"{year}{month:02}-citibike-tripdata.zip"
    url = f"{DATA_URL}/{file_name}"

    output_folder.mkdir(parents=True, exist_ok=True)
    expected_size = _fetch_expected_size(url)

    download_progress.start()
    download_task = download_progress.add_task(
        "Downloading data...", total=expected_size
    )
    unzip_task = unzip_progress.add_task("Unzipping data...", total=1)
    download_progress.update(download_task, description=f"Downloading {file_name}")
    with tempfile.NamedTemporaryFile() as temp:
        temp_path = pathlib.Path(temp.name)
        for file_bytes in _download_zip_file(
            f"{DATA_URL}/{year}{month:02}-citibike-tripdata.zip", temp_path
        ):
            download_progress.update(download_task, completed=file_bytes)
        download_progress.update(
            download_task,
            description="[green]✔[/green] Downloaded City Bike data successfully!",
        )
        download_progress.stop()
        unzip_progress.start()
        _unzip_file(temp_path, output_folder)
        unzip_progress.update(unzip_task, completed=1, description="Unzipped data!")
        unzip_progress.stop()
