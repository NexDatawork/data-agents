"""
AI Agents Module

This module contains the core AI agent implementations for NexDatawork.
Each agent specializes in a specific data processing task.

Agents:
    DataFrameAgent: Analyzes pandas DataFrames using natural language
    SQLAgent: Generates and executes SQL queries
    ETLAgent: Creates data transformation pipelines
    WebScrapingAgent: Extracts structured data from web pages
    AITools: Coordinator class that manages all agents

Usage:
    from src.agents import AITools
    
    tools = AITools(model=your_llm)
    result = tools.agent_analysis(files, question)
"""

from .dataframe_agent import DataFrameAgent, ask_agent
from .sql_agent import SQLAgent, create_db, sql_pipeline
from .etl_agent import ETLAgent, etl_pipeline
from .scraping_agent import WebScrapingAgent, web_scraping
from .coordinator import AITools

__all__ = [
    "DataFrameAgent",
    "ask_agent",
    "SQLAgent",
    "create_db",
    "sql_pipeline",
    "ETLAgent",
    "etl_pipeline",
    "WebScrapingAgent",
    "web_scraping",
    "AITools",
]
