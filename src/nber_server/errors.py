#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : nber_server/errors.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

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


async def api_error_handler(_request: Request, error: Exception) -> JSONResponse:
    api_error = cast(ApiError, error)
    return JSONResponse(
        status_code=api_error.status_code,
        content={
            "code": api_error.code,
            "data": api_error.data or {},
            "message": api_error.message,
        },
    )
