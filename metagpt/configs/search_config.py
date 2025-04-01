#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/1/4 19:06
@Author  : alexanderwu
@File    : search_config.py
"""
from typing import Callable, Optional

from pydantic import Field

from metagpt.tools import SearchEngineType
from metagpt.utils.yaml_model import YamlModel


class SearchConfig(YamlModel):
    """Config for Search"""

    api_type: SearchEngineType = SearchEngineType.SERPAPI_GOOGLE
    # api_key: str = "c230866334b218a6155769df8d1428764fa71c577784460c50564347d094fb9d"
    api_key: str = "8dc333797495c72a93a0c0520fe610bd390f90dfb5611ec8b198185b0e08df49"
    cse_id: str = ""  # for google
    search_func: Optional[Callable] = None
    params: dict = Field(
        default_factory=lambda: {
            "engine": "google",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
        }
    )
