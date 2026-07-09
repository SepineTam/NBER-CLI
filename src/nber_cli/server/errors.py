from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

SUCCESS_CODE = 0
PARAMETER_ERROR_CODE = 1
INTERNAL_ERROR_CODE = 2
EXTERNAL_SERVICE_ERROR_CODE = 3


@dataclass(slots=True)
class ApiError(Exception):
    status_code: int
    code: int
    message: str
    data: dict[str, Any] | None = None


def api_success(data: Any, message: str = "") -> dict[str, Any]:
    return {"code": SUCCESS_CODE, "data": data, "message": message}


async def api_error_handler(_request: Request, error: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "code": error.code,
            "data": error.data or {},
            "message": error.message,
        },
    )
