#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : conftest.py

from unittest.mock import patch

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")


@pytest.fixture(autouse=True)
def isolated_nber_home(tmp_path):
    with (
        patch("nber_cli.db.Path.home", return_value=tmp_path),
        patch("nber_cli.config_store.Path.home", return_value=tmp_path),
    ):
        yield tmp_path
