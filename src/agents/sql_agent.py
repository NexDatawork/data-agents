"""
SQL Query Generation Agent

This module implements the SQL agent that generates and executes SQL queries
against SQLite databases created from user-uploaded CSV files.

The agent uses LangGraph's ReAct pattern for reasoning and tool use,
combined with LangChain's SQLDatabaseToolkit for database operations.

Example:
    >>> from src.agents import sql_pipeline
    >>> result = sql_pipeline(files, "Show top 10 customers by revenue")
"""

import os
from typing import List, Optional, Any, Tuple

import pandas as pd
from sqlalchemy import create_engine

from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import create_react_agent

from ..prompts import get_sql_prompt


# Default database file path
DEFAULT_DB_PATH = "sqlite:///database.db"
DEFAULT_DB_FILE = "database.db"


class SQLAgent:
    """
    Agent for generating and executing SQL queries from natural language.
    
    This agent converts user questions into SQL queries, executes them
    against a SQLite database, and returns formatted results.
    
    Attributes:
        model: The LLM model for query generation.
        database: The SQLDatabase instance to query against.
        toolkit: SQLDatabaseToolkit providing database tools.
        
    Example:
        >>> agent = SQLAgent(model=azure_llm)
        >>> agent.load_files(csv_files)
        >>> result = agent.query("What are the top 5 products by sales?")
    """
    
    def __init__(self, model: Any):
        """
        Initialize the SQL agent.
        
        Args:
            model: The LLM model instance for query generation.
                   Must be a LangChain-compatible chat model.
        """
        self.model = model
        self.database: Optional[SQLDatabase] = None
        self.toolkit: Optional[SQLDatabaseToolkit] = None
    
    def load_files(self, files: List[Any]) -> bool:
        """
        Load CSV files into a SQLite database.
        
        Each CSV file becomes a table in the database, with the table name
        derived from the filename (without extension).
        
        Args:
            files: List of file objects with .name attribute pointing to CSV paths.
            
        Returns:
            bool: True if database creation succeeded, False otherwise.
            
        Example:
            >>> agent.load_files([file1, file2])
            True
        """
        try:
            # Create SQLite engine
            engine = create_engine(DEFAULT_DB_PATH)
            
            # Load each CSV as a table
            with engine.begin() as connection:
                for f in files:
                    # Extract table name from filename
                    table_name = os.path.splitext(os.path.basename(f.name))[0]
                    df = pd.read_csv(f.name)
                    
                    # Write DataFrame to SQL table (replace if exists)
                    df.to_sql(table_name, connection, if_exists="replace", index=False)
                    print(f"Loaded table: {table_name}")
            
            # Initialize SQLDatabase wrapper
            self.database = SQLDatabase.from_uri(DEFAULT_DB_PATH)
            
            # Create toolkit with database tools
            self.toolkit = SQLDatabaseToolkit(db=self.database, llm=self.model)
            
            print(f"Database created: {DEFAULT_DB_FILE}")
            return True
            
        except Exception as e:
            print(f"Database creation error: {e}")
            return False
    
    def query(self, question: str) -> str:
        """
        Execute a natural language query against the database.
        
        This method uses LangGraph's ReAct agent to:
        1. Inspect the database schema
        2. Generate an appropriate SQL query
        3. Execute the query
        4. Format and return the results
        
        Args:
            question: The natural language question about the data.
            
        Returns:
            str: The query results formatted in Markdown.
            
        Raises:
            ValueError: If database has not been loaded.
            
        Example:
            >>> result = agent.query("Show average order value by region")
        """
        if self.database is None or self.toolkit is None:
            raise ValueError("Database not loaded. Call load_files() first.")
        
        try:
            # Get tools from the toolkit
            tools = self.toolkit.get_tools()
            
            # Get the SQL system prompt
            system_prompt = get_sql_prompt()
            
            # Create ReAct agent for SQL operations
            agent_executor = create_react_agent(
                self.model,
                tools,
                prompt=system_prompt
            )
            
            # Execute the agent and collect output
            output = ""
            for step in agent_executor.stream(
                {"messages": [{"role": "user", "content": question}]},
                stream_mode="values",
            ):
                output += step["messages"][-1].content
            
            # Extract final answer section
            return self._extract_final_answer(output)
            
        except Exception as e:
            return f"SQL agent error: {e}"
    
    def _extract_final_answer(self, output: str) -> str:
        """
        Extract the final answer section from the agent output.
        
        Args:
            output: The full agent output string.
            
        Returns:
            str: The final answer section, or full output if not found.
        """
        marker = "### Final answer"
        pos = output.find(marker)
        if pos != -1:
            return output[pos:]
        return output


def create_db(files: List[Any]) -> Optional[SQLDatabase]:
    """
    Create a SQLite database from uploaded CSV files.
    
    This is a convenience function for creating databases without
    instantiating the full SQLAgent class.
    
    Args:
        files: List of file objects with .name attribute.
        
    Returns:
        SQLDatabase: The created database instance, or None on error.
        
    Example:
        >>> db = create_db(uploaded_files)
        >>> if db:
        ...     print(db.get_table_names())
    """
    try:
        engine = create_engine(DEFAULT_DB_PATH)
        
        with engine.begin() as connection:
            for f in files:
                table_name = os.path.splitext(os.path.basename(f.name))[0]
                df = pd.read_csv(f.name)
                df.to_sql(table_name, connection, if_exists="replace", index=False)
        
        return SQLDatabase.from_uri(DEFAULT_DB_PATH)
        
    except Exception as e:
        print(f"Database error: {e}")
        return None


def sql_pipeline(
    tables: List[Any],
    question: str,
    model: Optional[Any] = None
) -> str:
    """
    End-to-end pipeline for SQL query generation and execution.
    
    This function handles the complete workflow:
    1. Creates a SQLite database from uploaded files
    2. Initializes the SQL agent
    3. Generates and executes the query
    4. Returns formatted results
    
    Args:
        tables: List of file objects containing CSV data.
        question: The natural language question to answer.
        model: Optional LLM model. If None, uses global model.
        
    Returns:
        str: The query results in Markdown format.
        
    Example:
        >>> result = sql_pipeline(files, "Show monthly sales trends", model)
    """
    if model is None:
        return "Error: No LLM model provided."
    
    agent = SQLAgent(model=model)
    
    if not agent.load_files(tables):
        return "Error: Could not create database from files."
    
    return agent.query(question)
