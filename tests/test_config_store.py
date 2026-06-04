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
