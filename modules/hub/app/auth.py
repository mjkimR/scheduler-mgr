import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(x_api_key: str = Security(api_key_header)) -> None:
    """Verify the API key provided in the request header.

    Usage:
        APIRouter(..., dependencies=[Depends(verify_api_key)])

    NOTE: Currently disabled as GCP Cloud Run's built-in authentication is used.
    """
    secret_key = os.environ.get("APP_SECRET_KEY")
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APP_SECRET_KEY is not configured.",
        )
    if x_api_key != secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
