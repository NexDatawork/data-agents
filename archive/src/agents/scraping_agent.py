"""
Web Scraping Agent

This module implements the AI-powered web scraping agent that extracts
structured data from web pages using the SmartScraperTool.

The agent uses natural language instructions to:
1. Identify target data based on keywords
2. Extract specified quantities of items
3. Structure results as pandas DataFrames

Example:
    >>> from src.agents import web_scraping
    >>> result = web_scraping("Find top 5 AI startups and their funding")
"""

import io
import contextlib
from typing import Optional, Any

from langchain.agents import initialize_agent, AgentType

from ..prompts import get_scraping_prompt


class WebScrapingAgent:
    """
    Agent for AI-powered web data extraction.
    
    This agent uses SmartScraperTool to extract structured data from
    web pages based on natural language descriptions.
    
    Attributes:
        model: The LLM model for understanding extraction requests.
        tools: List of scraping tools (SmartScraperTool).
        
    Example:
        >>> agent = WebScrapingAgent(model=azure_llm)
        >>> data = agent.scrape("List 10 popular Python libraries")
    """
    
    def __init__(self, model: Any):
        """
        Initialize the web scraping agent.
        
        Args:
            model: The LLM model instance for understanding requests.
        
        Note:
            Requires SGAI_API_KEY environment variable to be set
            for SmartScraperTool functionality.
        """
        self.model = model
        self.tools = self._create_tools()
    
    def _create_tools(self):
        """
        Create the web scraping tools.
        
        Returns:
            List of LangChain tools for web scraping.
            
        Note:
            SmartScraperTool requires langchain-scrapegraph package
            and a valid ScrapeGraphAI API key.
        """
        try:
            from langchain_scrapegraph.tools import SmartScraperTool
            return [SmartScraperTool()]
        except ImportError:
            print("Warning: langchain-scrapegraph not installed")
            return []
    
    def scrape(self, query: str) -> str:
        """
        Extract data from the web based on a natural language query.
        
        This method:
        1. Parses the query to identify keywords and quantities
        2. Formulates targeted search queries
        3. Extracts and structures the data
        4. Returns results as a formatted string (ideally DataFrame-ready)
        
        Args:
            query: Natural language description of data to extract.
                   Example: "Find top 10 AI companies and their funding"
                   
        Returns:
            str: Extracted data in structured format, or error message.
            
        Example:
            >>> result = agent.scrape("List 5 trending GitHub repos")
        """
        if not self.tools:
            return "Error: Web scraping tools not available. Install langchain-scrapegraph."
        
        try:
            # Create structured agent for web scraping
            agent = initialize_agent(
                tools=self.tools,
                llm=self.model,
                agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
            
            # Build the full prompt with scraping instructions
            full_prompt = get_scraping_prompt(query)
            
            # Capture output during execution
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                response = agent.run(full_prompt)
            
            return response
            
        except Exception as e:
            return f"Web scraping error: {e}"


def web_scraping(
    question: str,
    model: Optional[Any] = None
) -> str:
    """
    Extract data from the web using natural language instructions.
    
    This is a convenience function that wraps WebScrapingAgent
    for simple extraction tasks.
    
    Args:
        question: Natural language description of data to extract.
        model: Optional LLM model. If None, uses global model.
        
    Returns:
        str: Extracted data or error message.
        
    Example:
        >>> data = web_scraping("Find 5 popular ML frameworks", model)
    """
    if model is None:
        return "Error: No LLM model provided."
    
    agent = WebScrapingAgent(model=model)
    return agent.scrape(question)
