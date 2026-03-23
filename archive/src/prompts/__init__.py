"""
Prompt Templates Module

This module contains all LLM prompt templates used by the NexDatawork agents.
Prompts are organized by agent type and can be customized for different use cases.

Usage:
    from src.prompts import CSV_PROMPT_PREFIX, CSV_PROMPT_SUFFIX
    from src.prompts import get_analysis_prompt
"""

from .analysis_prompts import (
    CSV_PROMPT_PREFIX,
    CSV_PROMPT_SUFFIX,
    get_analysis_prompt,
)

from .sql_prompts import (
    SQL_SYSTEM_MESSAGE,
    SQL_SUFFIX_PROMPT,
    get_sql_prompt,
)

from .scraping_prompts import (
    SCRAPING_PROMPT_PREFIX,
    SCRAPING_PROMPT_SUFFIX,
    get_scraping_prompt,
)

__all__ = [
    "CSV_PROMPT_PREFIX",
    "CSV_PROMPT_SUFFIX",
    "get_analysis_prompt",
    "SQL_SYSTEM_MESSAGE",
    "SQL_SUFFIX_PROMPT",
    "get_sql_prompt",
    "SCRAPING_PROMPT_PREFIX",
    "SCRAPING_PROMPT_SUFFIX",
    "get_scraping_prompt",
]
