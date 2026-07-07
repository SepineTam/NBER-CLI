#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : config_store.py

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ConfigValue = Any
ConfigDict = dict[str, ConfigValue]

_CLI_CONFIG_PATH: Path | None = None

NBER_CLI_DIR_NAME = ".nber-cli"
NBER_CLI_CONFIG_NAME = "config.json"
NBER_DB_NAME = "nber.db"
LEGACY_DB_NAME = "feed.db"

DEFAULT_INFO_CACHE_ENABLED = True
DEFAULT_INFO_CACHE_TTL_DAYS = 30

_DEFAULT_CONFIG: ConfigDict = {
    "info": {"cache_enabled": DEFAULT_INFO_CACHE_ENABLED, "cache_ttl_days": DEFAULT_INFO_CACHE_TTL_DAYS},
    "download": {"restrict_dir": True, "concurrency": 3},
}


@dataclass(frozen=True, slots=True)
class InfoCacheSettings:
    cache_enabled: bool = DEFAULT_INFO_CACHE_ENABLED
    cache_ttl_days: int = DEFAULT_INFO_CACHE_TTL_DAYS


def set_cli_config_path(path: Path | str | None) -> None:
    global _CLI_CONFIG_PATH
    _CLI_CONFIG_PATH = Path(path) if path is not None else None


def clear_cli_config_path() -> None:
    global _CLI_CONFIG_PATH
    _CLI_CONFIG_PATH = None


def default_config_path() -> Path:
    if _CLI_CONFIG_PATH is not None:
        return _CLI_CONFIG_PATH
    return Path.home() / NBER_CLI_DIR_NAME / NBER_CLI_CONFIG_NAME


def default_db_path() -> Path:
    return Path.home() / NBER_CLI_DIR_NAME / NBER_DB_NAME


def legacy_db_path() -> Path:
    return Path.home() / NBER_CLI_DIR_NAME / LEGACY_DB_NAME


def _inject_defaults(config: ConfigDict) -> None:
    for key, default_value in _DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = copy.deepcopy(default_value)
            continue
        if isinstance(default_value, dict) and isinstance(config.get(key), dict):
            for sub_key, sub_default in default_value.items():
                if sub_key not in config[key]:
                    config[key][sub_key] = copy.deepcopy(sub_default)


def get_config_value(config: ConfigDict, dot_path: str) -> ConfigValue:
    keys = dot_path.split(".")
    current: ConfigValue = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def set_config_value(config: ConfigDict, dot_path: str, value: ConfigValue) -> None:
    keys = dot_path.split(".")
    current = config
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def validate_config(config: ConfigValue) -> list[str]:
    errors: list[str] = []
    schema = _load_schema()
    if schema is None:
        return errors
    _validate_against_schema(config, schema, "$", errors)
    return errors


def _load_schema() -> ConfigDict | None:
    import importlib.resources

    try:
        schema_text = importlib.resources.files("nber_cli").joinpath("config.schema.json").read_text()
        schema = json.loads(schema_text)
        return schema if isinstance(schema, dict) else None
    except (OSError, json.JSONDecodeError, ImportError):
        return None


def _validate_against_schema(
    value: ConfigValue,
    schema: ConfigDict,
    path: str,
    errors: list[str],
) -> None:
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{path}: expected object, got {type(value).__name__}")
            return
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            return
        for key, prop_schema in properties.items():
            if not isinstance(prop_schema, dict):
                continue
            if key in value:
                _validate_against_schema(value[key], prop_schema, f"{path}.{key}", errors)
        return
    if schema_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{path}: expected integer, got {type(value).__name__}")
            return
        minimum = schema.get("minimum")
        if isinstance(minimum, int) and value < minimum:
            errors.append(f"{path}: must be greater than or equal to {minimum}")
        return
    if schema_type == "boolean" and not isinstance(value, bool):
        errors.append(f"{path}: expected boolean, got {type(value).__name__}")
    elif schema_type == "string" and not isinstance(value, str):
        errors.append(f"{path}: expected string, got {type(value).__name__}")


def read_config_for_validation(config_path: Path | None = None) -> ConfigValue:
    resolved_path = config_path or default_config_path()
    if not resolved_path.exists():
        return {}
    try:
        return json.loads(resolved_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"failed to read config from {resolved_path}: {error.__class__.__name__}"
        ) from error


def read_config(config_path: Path | None = None) -> ConfigDict:
    resolved_path = config_path or default_config_path()
    if not resolved_path.exists():
        config: ConfigDict = {}
    else:
        try:
            loaded = json.loads(resolved_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            import warnings

            warnings.warn(f"failed to read config from {resolved_path}: {error.__class__.__name__}")
            loaded = None
        config = loaded if isinstance(loaded, dict) else {}

    _inject_defaults(config)
    return config


def write_config(config: ConfigDict, config_path: Path | None = None) -> None:
    resolved_path = config_path or default_config_path()
    try:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    except OSError as error:
        raise RuntimeError(f"failed to write config to {resolved_path}: {error.__class__.__name__}") from error


def update_database_config(
    db_path: Path,
    schema_version: int,
    config_path: Path | None = None,
) -> None:
    config = read_config(config_path)
    config["schema_version"] = schema_version
    feed_config = config.get("feed")
    if not isinstance(feed_config, dict):
        feed_config = {}
    feed_config["db-path"] = str(db_path)
    config["feed"] = feed_config
    write_config(config, config_path)


def get_configured_db_path(config_path: Path | None = None) -> Path | None:
    config = read_config(config_path)
    feed_config = config.get("feed")
    if not isinstance(feed_config, dict):
        return None

    db_path = feed_config.get("db-path")
    if isinstance(db_path, str) and db_path.strip():
        return Path(db_path)
    return None


def get_info_cache_settings(config_path: Path | None = None) -> InfoCacheSettings:
    config = read_config(config_path)
    info_config = config.get("info")
    if not isinstance(info_config, dict):
        info_config = {}

    cache_enabled = _coerce_bool(
        info_config.get("cache_enabled"),
        DEFAULT_INFO_CACHE_ENABLED,
    )
    cache_ttl_days = _coerce_positive_int(
        info_config.get("cache_ttl_days"),
        DEFAULT_INFO_CACHE_TTL_DAYS,
    )
    return InfoCacheSettings(
        cache_enabled=cache_enabled,
        cache_ttl_days=cache_ttl_days,
    )


def set_info_cache_enabled(
    cache_enabled: bool,
    config_path: Path | None = None,
) -> InfoCacheSettings:
    config = read_config(config_path)
    info_config = _get_mutable_info_config(config)
    info_config["cache_enabled"] = cache_enabled
    write_config(config, config_path)
    return get_info_cache_settings(config_path)


def set_info_cache_ttl_days(
    cache_ttl_days: int,
    config_path: Path | None = None,
) -> InfoCacheSettings:
    if cache_ttl_days <= 0:
        raise ValueError("cache_ttl_days must be a positive integer")

    config = read_config(config_path)
    info_config = _get_mutable_info_config(config)
    info_config["cache_ttl_days"] = cache_ttl_days
    write_config(config, config_path)
    return get_info_cache_settings(config_path)


def _get_mutable_info_config(config: ConfigDict) -> ConfigDict:
    info_config = config.get("info")
    if not isinstance(info_config, dict):
        info_config = {}
    config["info"] = info_config
    return info_config


def _coerce_bool(value: ConfigValue, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _coerce_positive_int(value: ConfigValue, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return default
