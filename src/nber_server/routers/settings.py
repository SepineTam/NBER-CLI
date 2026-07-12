from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import ValidationError

from nber_cli import config_store
from nber_server.errors import ApiError, PARAMETER_ERROR_CODE, api_success
from nber_server.schemas import SettingsPatch, SettingsResponse

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("")
async def get_settings(request: Request):
    return api_success(_settings_response(request).model_dump())


@router.patch("")
async def update_settings(payload: SettingsPatch, request: Request):
    try:
        config_store.set_desktop_settings(
            server_port=payload.server_port,
            feed_refresh_interval_minutes=payload.feed_refresh_interval_minutes,
        )
    except (ValueError, ValidationError) as error:
        raise ApiError(
            status_code=400,
            code=PARAMETER_ERROR_CODE,
            message=str(error),
        ) from error
    return api_success(_settings_response(request).model_dump())


def _settings_response(request: Request) -> SettingsResponse:
    settings = config_store.get_desktop_settings()
    log_dir = Path(request.app.state.log_dir)
    return SettingsResponse(
        server_port=settings.server_port,
        feed_refresh_interval_minutes=settings.feed_refresh_interval_minutes,
        config_path=str(config_store.default_config_path()),
        db_path=str(Path(request.app.state.db_path)),
        log_dir=str(log_dir),
    )
