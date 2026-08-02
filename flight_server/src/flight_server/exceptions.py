from collections.abc import Callable
from functools import wraps

import structlog
from pyarrow import flight

logger = structlog.get_logger(__name__)


class FlightServerException(Exception):
    pass


class IcebergCatalogueException(FlightServerException):
    pass


def handle_flight_errors(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except flight.FlightError:
            raise
        except Exception as e:
            logger.exception("unhandled error in flight endpoint")
            raise flight.FlightServerError(str(e)) from e

    return wrapper
