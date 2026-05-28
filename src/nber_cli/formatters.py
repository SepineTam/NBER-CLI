#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : formatters.py

from typing import Dict

from .core.models import NBER


def paper_id_str(paper: NBER) -> str:
    return f"w{paper.paper_id:04d}"


def info(paper: NBER) -> Dict:
    return {
        "id": paper_id_str(paper),
        "title": paper.title,
        "authors": paper.authors,
        "date": paper.date,
        "abstract": paper.abstract,
    }


def related(paper: NBER) -> Dict[str, str | None]:
    return {
        "topic": paper.topic,
        "programs": paper.programs,
    }
