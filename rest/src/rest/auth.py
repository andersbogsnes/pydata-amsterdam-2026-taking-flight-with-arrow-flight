import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

auth = HTTPBearer(auto_error=False)


def verify_user(
    request: Request,
    bearer_token: Annotated[HTTPAuthorizationCredentials | None, Depends(auth)],
):
    if request.url.path in ("/health", "/", "/docs"):
        return

    if bearer_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if secrets.compare_digest(bearer_token.credentials, "pydata_amsterdam"):
        return

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
