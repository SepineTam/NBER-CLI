#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : test_config_store.py

import json

import pytest

from nber_cli import config_store
from nber_cli.config import NBERCLIConfig


class TestInfoCacheSettings:
    def test_defaults_when_config_is_missing(self):
        settings = config_store.get_info_cache_settings()

        assert settings.cache_enabled is True
        assert settings.cache_ttl_days == 30

    def test_defaults_when_info_section_is_missing(self, isolated_nber_home):
        config_path = isolated_nber_home / ".nber-cli" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(json.dumps({"schema_version": 2}))

        settings = config_store.get_info_cache_settings()

        assert settings.cache_enabled is True
        assert settings.cache_ttl_days == 30

    def test_defaults_when_values_have_wrong_type(self, isolated_nber_home):
        config_path = isolated_nber_home / ".nber-cli" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps(
                {
                    "info": {
                        "cache_enabled": "yes",
                        "cache_ttl_days": "30",
                    }
                }
            )
        )

        settings = config_store.get_info_cache_settings()

        assert settings.cache_enabled is True
        assert settings.cache_ttl_days == 30

    def test_defaults_when_config_json_is_invalid(self, isolated_nber_home):
        config_path = isolated_nber_home / ".nber-cli" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("{")

        with pytest.warns(UserWarning, match="failed to read config"):
            settings = config_store.get_info_cache_settings()

        assert settings.cache_enabled is True
        assert settings.cache_ttl_days == 30

    def test_set_info_cache_enabled_preserves_existing_config(self, isolated_nber_home):
        config_path = isolated_nber_home / ".nber-cli" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "feed": {"db-path": "/tmp/nber.db"},
                    "info": {"cache_ttl_days": 12},
                }
            )
        )

        settings = config_store.set_info_cache_enabled(False)
        config = json.loads(config_path.read_text())

        assert settings.cache_enabled is False
        assert settings.cache_ttl_days == 12
        assert config["schema_version"] == 2
        assert config["feed"]["db-path"] == "/tmp/nber.db"
        assert config["info"]["cache_enabled"] is False
        assert config["info"]["cache_ttl_days"] == 12

    def test_set_info_cache_ttl_days_rejects_non_positive_value(self):
        with pytest.raises(ValueError, match="positive"):
            config_store.set_info_cache_ttl_days(0)


class TestNestedConfigOperations:
    def test_get_nested_value(self):
        config = {"download": {"restrict_dir": True}}
        assert config_store.get_config_value(config, "download.restrict_dir") is True
        assert config_store.get_config_value(config, "download") == {"restrict_dir": True}

    def test_get_missing_returns_none(self):
        config = {"download": {"restrict_dir": True}}
        assert config_store.get_config_value(config, "download.missing") is None
        assert config_store.get_config_value(config, "nonexistent.key") is None

    def test_set_nested_value_creates_intermediate_dicts(self):
        config: dict = {}
        config_store.set_config_value(config, "a.b.c", 42)
        assert config == {"a": {"b": {"c": 42}}}

    def test_set_overwrites_existing_value(self):
        config = {"download": {"restrict_dir": True}}
        config_store.set_config_value(config, "download.restrict_dir", False)
        assert config["download"]["restrict_dir"] is False


class TestInjectDefaults:
    def test_injects_missing_top_level_keys(self):
        config: dict = {}
        config_store._inject_defaults(config)
        assert "info" in config
        assert "download" in config
        assert config["download"]["restrict_dir"] is True

    def test_injects_missing_nested_keys_without_overwriting(self):
        config = {"info": {"cache_enabled": False}}
        config_store._inject_defaults(config)
        assert config["info"]["cache_enabled"] is False
        assert config["info"]["cache_ttl_days"] == 30

    def test_deep_copy_prevents_pollution(self):
        config1: dict = {}
        config_store._inject_defaults(config1)
        config1["info"]["cache_enabled"] = False

        config2: dict = {}
        config_store._inject_defaults(config2)
        assert config2["info"]["cache_enabled"] is True


class TestValidateConfig:
    def test_valid_config_passes(self):
        config = {
            "schema_version": 2,
            "info": {"cache_enabled": True, "cache_ttl_days": 30},
            "feed": {"db-path": "/tmp/nber.db"},
            "download": {"restrict_dir": True},
        }
        errors = config_store.validate_config(config)
        assert errors == []

    def test_detects_wrong_types(self):
        config = {
            "info": {"cache_enabled": "yes", "cache_ttl_days": "thirty"},
            "feed": {"db-path": 123},
        }
        errors = config_store.validate_config(config)
        assert len(errors) == 3
        assert any("info.cache_enabled: expected boolean" in e for e in errors)
        assert any("info.cache_ttl_days: expected integer" in e for e in errors)
        assert any("feed.db-path: expected string" in e for e in errors)

    def test_empty_config_passes(self):
        errors = config_store.validate_config({})
        assert errors == []

    def test_returns_empty_when_config_is_valid(self):
        errors = config_store.validate_config({"info": {"cache_enabled": True}})
        assert errors == []

    @pytest.mark.parametrize("config", [[], 1, None])
    def test_rejects_non_object_root(self, config):
        errors = config_store.validate_config(config)

        assert errors == [f"$: expected object, got {type(config).__name__}"]

    def test_rejects_non_object_section(self):
        errors = config_store.validate_config({"download": []})

        assert errors == ["$.download: expected object, got list"]

    @pytest.mark.parametrize("value", [0, -1])
    def test_enforces_minimum(self, value):
        errors = config_store.validate_config(
            {"download": {"concurrency": value}, "info": {"cache_ttl_days": value}}
        )

        assert "$.download.concurrency: must be greater than or equal to 1" in errors
        assert "$.info.cache_ttl_days: must be greater than or equal to 1" in errors

    def test_rejects_boolean_as_integer(self):
        errors = config_store.validate_config({"download": {"concurrency": True}})

        assert errors == ["$.download.concurrency: expected integer, got bool"]

    def test_rejects_null_scalar(self):
        errors = config_store.validate_config({"info": {"cache_enabled": None}})

        assert errors == ["$.info.cache_enabled: expected boolean, got NoneType"]


class TestReadConfigForValidation:
    def test_returns_raw_json_without_defaults(self, isolated_nber_home):
        config_path = isolated_nber_home / ".nber-cli" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("[]")

        assert config_store.read_config_for_validation() == []

    def test_rejects_malformed_json(self, isolated_nber_home):
        config_path = isolated_nber_home / ".nber-cli" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("{")

        with pytest.raises(ValueError, match="JSONDecodeError"):
            config_store.read_config_for_validation()


class TestRuntimeConfig:
    @pytest.mark.parametrize("concurrency", [0, -1, True])
    def test_invalid_concurrency_uses_safe_default(self, concurrency, monkeypatch):
        monkeypatch.setattr(
            config_store,
            "read_config",
            lambda: {"download": {"concurrency": concurrency}},
        )

        assert NBERCLIConfig.from_config_file().download_concurrency == 3
