#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : test_main.py

import sys
from unittest.mock import patch


class TestMainEntryPoint:
    def test_main_imports_and_runs(self):
        with patch.object(sys, "argv", ["nber-cli"]):
            with patch("nber_cli.main") as mock_cli_main:
                mock_cli_main.return_value = None
                import nber_cli.__main__
                nber_cli.__main__.main()
                mock_cli_main.assert_called_once()
