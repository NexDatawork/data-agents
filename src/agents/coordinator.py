"""
AI Tools Coordinator

This module implements the AITools class that coordinates all AI agents
and maintains conversation history for the NexDatawork platform.

The coordinator provides a unified interface for:
- DataFrame analysis
- SQL query generation
- ETL pipeline creation
- Web scraping

Example:
    >>> from src.agents import AITools
    >>> tools = AITools(model=azure_llm)
    >>> tools.agent_analysis(files, "Summarize sales trends")
"""

from typing import List, Optional, Any

from .dataframe_agent import ask_agent
from .sql_agent import sql_pipeline
from .etl_agent import etl_pipeline
from .scraping_agent import web_scraping


class AITools:
    """
    Coordinator class that manages all AI agents and their outputs.
    
    This class provides a unified interface for invoking different
    AI agents and maintains a history of their outputs for reference.
    
    Attributes:
        model: The LLM model shared across all agents.
        analysis: Accumulated output from analysis operations.
        sql_etl: Accumulated output from SQL and ETL operations.
        
    Example:
        >>> tools = AITools(model=azure_llm)
        >>> 
        >>> # Analyze data
        >>> result = tools.agent_analysis(files, "What are the trends?")
        >>> 
        >>> # Generate SQL
        >>> sql = tools.SQL(files, "Show top customers")
        >>> 
        >>> # All results are accumulated in tools.analysis and tools.sql_etl
    """
    
    def __init__(self, model: Optional[Any] = None):
        """
        Initialize the AI Tools coordinator.
        
        Args:
            model: The LLM model to use for all agents.
                   Required for agent operations.
                   
        Note:
            The analysis and sql_etl attributes accumulate outputs
            across multiple operations, providing a history of results.
        """
        self.model = model
        
        # History storage for different operation types
        # Analysis results (DataFrame analysis, web scraping)
        self.analysis: str = ""
        
        # SQL and ETL pipeline results
        self.sql_etl: str = ""
    
    def SQL(self, tables: List[Any], question: str) -> str:
        """
        Generate and execute SQL queries from natural language.
        
        This method:
        1. Creates a SQLite database from uploaded files
        2. Generates SQL query from the question
        3. Executes query and formats results
        4. Appends results to sql_etl history
        
        Args:
            tables: List of file objects containing CSV data.
            question: Natural language question about the data.
            
        Returns:
            str: Accumulated SQL/ETL outputs including this query.
            
        Example:
            >>> result = tools.SQL(files, "Show monthly revenue")
        """
        try:
            final_answer = sql_pipeline(tables, question, self.model)
            print(final_answer)
            
            # Append to history
            self.sql_etl += final_answer + "\n"
            return self.sql_etl
            
        except Exception as e:
            error_msg = f"Impossible to generate SQL query: {e}"
            return error_msg
    
    def ETL(self, dataframe: List[Any]) -> str:
        """
        Generate ETL transformation pipeline code.
        
        This method creates Python/pandas code for cleaning
        and transforming the uploaded data.
        
        Args:
            dataframe: List of file objects to process.
            
        Returns:
            str: Accumulated SQL/ETL outputs including generated code.
            
        Example:
            >>> code = tools.ETL(raw_files)
            >>> exec(code)  # Apply transformations
        """
        try:
            final_answer = etl_pipeline(dataframe, self.model)
            print(final_answer)
            
            # Append to history
            self.sql_etl += final_answer + "\n"
            return self.sql_etl
            
        except Exception as e:
            error_msg = f"Impossible to generate ETL pipeline: {e}"
            return error_msg
    
    def agent_analysis(self, files: List[Any], question: str) -> str:
        """
        Perform AI-powered data analysis on uploaded files.
        
        This method uses the DataFrame agent to analyze data
        and answer natural language questions.
        
        Args:
            files: List of file objects containing CSV data.
            question: Natural language question about the data.
            
        Returns:
            str: Accumulated analysis outputs including this result.
            
        Example:
            >>> insights = tools.agent_analysis(files, "Find anomalies")
        """
        try:
            final_answer = ask_agent(files, question, self.model)
            print(final_answer)
            
            # Append to history
            self.analysis += final_answer + "\n"
            return self.analysis
            
        except Exception as e:
            error_msg = f"Impossible to generate analysis: {e}"
            return error_msg
    
    def web(self, question: str) -> str:
        """
        Extract data from the web using AI-powered scraping.
        
        This method uses the web scraping agent to find and
        extract structured data from web pages.
        
        Args:
            question: Natural language description of data to find.
                      Example: "Find top 10 AI companies and funding"
                      
        Returns:
            str: Accumulated analysis outputs including scraped data.
            
        Example:
            >>> data = tools.web("List 5 trending ML libraries")
        """
        try:
            final_answer = web_scraping(question, self.model)
            print(final_answer)
            
            # Append to analysis history (web data is analysis-related)
            self.analysis += final_answer + "\n"
            return self.analysis
            
        except Exception as e:
            error_msg = f"Impossible to return output: {e}"
            return error_msg
    
    def clear_history(self) -> None:
        """
        Clear all accumulated outputs.
        
        Use this to reset the history before starting a new
        analysis session.
        
        Example:
            >>> tools.clear_history()
            >>> tools.agent_analysis(new_files, "Fresh analysis")
        """
        self.analysis = ""
        self.sql_etl = ""
    
    def get_full_history(self) -> str:
        """
        Get all accumulated outputs from both analysis and SQL/ETL.
        
        Returns:
            str: Combined history of all operations.
            
        Example:
            >>> history = tools.get_full_history()
            >>> save_to_file(history, "session_log.md")
        """
        return f"=== Analysis History ===\n{self.analysis}\n\n=== SQL/ETL History ===\n{self.sql_etl}"
