from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class NotFoundError(HTTPException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(status_code=404, detail=f"{resource} {resource_id} not found")


class ConflictError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail)


class ValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)


class InsufficientDataError(HTTPException):
    def __init__(self, missing_domains: list[str]):
        super().__init__(
            status_code=400,
            detail={
                "message": "Insufficient data to perform this operation",
                "missing_domains": missing_domains,
            },
        )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
