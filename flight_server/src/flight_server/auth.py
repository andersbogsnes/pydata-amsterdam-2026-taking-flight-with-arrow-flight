import json
from logging import getLogger

from pyarrow import flight

# These types are not yet exported as public types https://github.com/apache/arrow/issues/44909
from pyarrow._flight import (  # type: ignore
    ClientAuthReader,
    ClientAuthSender,
    ServerAuthReader,
    ServerAuthSender,
)

logger = getLogger(__name__)


class TokenServerAuthHandler(flight.ServerAuthHandler):
    def __init__(self, token: str):
        super().__init__()
        self._token = token.encode("utf-8")

    def authenticate(
        self, outgoing: ServerAuthSender, incoming: ServerAuthReader
    ) -> None:
        """This is called by the Flight server when a new connection is established."""
        logger.info("Authenticating user during handshake")
        received = incoming.read()

        if received != self._token:
            raise flight.FlightUnauthenticatedError("Invalid token")
        logger.info("Token is valid - returning valid token")
        outgoing.write(received)

    def is_valid(self, token) -> str:
        """This is called by the Flight server to check if a token is still valid."""
        if not token:
            logger.info("No token provided, assuming user")
            # For demo purposes, we allow anyone to connect
            return json.dumps({"user": "myuser", "role": "user"})
        if token != self._token:
            raise flight.FlightUnauthenticatedError("Invalid token")
        logger.info("Token is valid - returning admin role")
        return json.dumps({"user": "myuser", "role": "admin"})


class TokenClientAuthHandler(flight.ClientAuthHandler):
    def __init__(self, token: str):
        super().__init__()
        self._token = token

    def get_token(self) -> bytes:
        return self._token.encode("utf-8")

    def authenticate(self, outgoing: ClientAuthSender, incoming: ClientAuthReader):
        outgoing.write(self._token.encode("utf-8"))
        incoming.read()
