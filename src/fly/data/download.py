import pathlib
import zipfile
from collections.abc import Iterator

import httpx2


def _download_zip_file(url: str, output_file: pathlib.Path) -> Iterator[int]:
    """Downloads a zip file from the given URL and saves it to the specified output file.
    Yields the number of bytes downloaded for use in progress bars."""
    with httpx2.stream("GET", url) as resp:
        resp.raise_for_status()
        with output_file.open("wb") as f:
            bytes_read = 0
            for chunk in resp.iter_bytes():
                f.write(chunk)
                bytes_read += len(chunk)
                yield bytes_read


def _unzip_file(zip_file: pathlib.Path, output_dir: pathlib.Path) -> None:
    """Unzips a zip file to the specified output directory."""
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(output_dir)

def _fetch_expected_size(url: str) -> int:
    """Fetches the expected size of the file from the given URL."""
    resp = httpx2.head(url)
    resp.raise_for_status()
    return int(resp.headers["Content-Length"])
