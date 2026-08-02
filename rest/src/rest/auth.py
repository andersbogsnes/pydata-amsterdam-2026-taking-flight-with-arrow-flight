import secrets
from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

auth = HTTPBearer()


def verify_user(bearer_token: Annotated[HTTPAuthorizationCredentials, Depends(auth)]):
    if secrets.compare_digest(bearer_token.credentials, "pydatamstedam"):
        return
    else:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
