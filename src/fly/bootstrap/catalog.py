import httpx2

from fly.console import console
from fly.settings import Settings


def _bootstrap_project(client: httpx2.Client) -> None:
    resp = client.post("/management/v1/bootstrap", json={"accept-terms-of-use": True})

    match resp.status_code:
        case 204:
            console.print("[green]✔[/green] Catalog bootstrapped successfully")
        case 400:
            match resp.json():
                case {"error": {"type": "CatalogAlreadyBootstrapped"}}:
                    console.print("[green]✔[/green] Catalog already bootstrapped")
                case message:
                    console.print(message)
                    raise RuntimeError("Failed to bootstrap catalog")
        case _:
            console.print(resp.text)
            raise RuntimeError("Failed to bootstrap catalog")


def _bootstrap_warehouse(client: httpx2.Client, settings: Settings) -> None:
    resp = client.post(
        "/management/v1/warehouse",
        json={
            "warehouse-name": "default",
            "default-format-version": 3,
            "storage-profile": {
                "type": "s3",
                "bucket": settings.bucket_name,
                "key-prefix": "iceberg",
                "path-style-access": True,
                "endpoint": settings.s3_catalog_endpoint,
                "region": settings.s3_region,
                "flavor": "s3-compat",
                "sts-enabled": True,
                "sts-endpoint": settings.s3_catalog_endpoint,
                "remote-signing-enabled": False,
            },
            "storage-credential": {
                "type": "s3",
                "credential-type": "access-key",
                "aws-access-key-id": settings.s3_access_key.get_secret_value(),
                "aws-secret-access-key": settings.s3_secret_key.get_secret_value(),
            },
            "delete-profile": {
                "type": "hard",
            },
        },
    )

    match resp.status_code:
        case 201:
            console.print("[green]✔[/green] Warehouse bootstrapped successfully")
        case 400:
            match resp.json():
                case {"error": {"type": "CreateWarehouseStorageProfileOverlap"}}:
                    console.print("[green]✔[/green] Warehouse already bootstrapped")
                case message:
                    console.print(message)
                    raise RuntimeError(f"Failed to bootstrap warehouse: {message}")
        case _:
            console.print(resp.text)
            raise RuntimeError(f"Failed to bootstrap catalog: {resp.text}")


def _bootstrap_catalog(settings: Settings) -> None:
    with httpx2.Client(base_url=settings.catalog_url) as client:
        _bootstrap_project(client)
        _bootstrap_warehouse(client, settings)
