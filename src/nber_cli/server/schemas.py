from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FeedItemResponse(BaseModel):
    paper_id: str
    title: str
    authors: list[str]
    abstract: str
    url: str
    source_url: str
    guid: str
    first_seen_at: str
    last_seen_at: str
    is_read: bool = False


class FeedListResponse(BaseModel):
    items: list[FeedItemResponse]
    total_count: int
    limit: int
    offset: int
    last_successful_fetch_at: str | None = None


class FeedRefreshResponse(BaseModel):
    new_count: int
    total_count: int
    fetched_count: int
    last_successful_fetch_at: str | None = None


class PaperResponse(BaseModel):
    paper_id: str
    title: str
    authors: list[str]
    date: str
    abstract: str
    url: str | None = None
    pdf_url: str | None = None
    published_version: str | None = None
    topic: str | None = None
    programs: str | None = None
    is_read: bool = False
    from_cache: bool = False


class ReadStatusUpdate(BaseModel):
    is_read: bool = True


class ReadStatusResponse(BaseModel):
    paper_id: str
    is_read: bool


class SettingsResponse(BaseModel):
    server_port: int
    feed_refresh_interval_minutes: int
    config_path: str
    db_path: str
    log_dir: str


class SettingsPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server_port: int | None = Field(default=None, ge=1024, le=65535)
    feed_refresh_interval_minutes: int | None = Field(default=None, ge=1)


class HealthResponse(BaseModel):
    status: str
    version: str
    db_path: str


ApiData = dict[str, Any] | list[Any] | BaseModel
