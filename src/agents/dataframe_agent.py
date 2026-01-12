"""
DataFrame Analysis Agent

This module implements the pandas DataFrame analysis agent that processes
CSV files and answers natural language questions about the data.

The agent uses LangChain's create_pandas_dataframe_agent to enable
natural language interaction with pandas DataFrames.

Example:
    >>> from src.agents import ask_agent
    >>> result = ask_agent(files, "What is the average revenue by region?")
"""

import io
import contextlib
from typing import List, Optional, Any

import pandas as pd
from langchain.agents import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from ..prompts import get_analysis_prompt


class DataFrameAgent:
    """
    Agent for analyzing pandas DataFrames using natural language queries.
    
    This agent wraps LangChain's pandas DataFrame agent and provides
    a simplified interface for data analysis tasks.
    
    Attributes:
        model: The LLM model to use for inference (e.g., AzureChatOpenAI).
        verbose: Whether to enable verbose logging for debugging.
        
    Example:
        >>> agent = DataFrameAgent(model=azure_llm)
        >>> df = pd.read_csv("sales.csv")
        >>> result = agent.analyze(df, "What are the top 5 products by revenue?")
    """
    
    def __init__(self, model: Any, verbose: bool = True):
        """
        Initialize the DataFrame agent.
        
        Args:
            model: The LLM model instance to use for inference.
                   Must be a LangChain-compatible chat model.
            verbose: Enable verbose output for debugging (default: True).
        """
        self.model = model
        self.verbose = verbose
    
    def analyze(self, df: pd.DataFrame, question: str) -> str:
        """
        Analyze a DataFrame and answer a natural language question.
        
        This method creates a LangChain pandas agent, constructs the full
        prompt, and invokes the agent to generate insights.
        
        Args:
            df: The pandas DataFrame to analyze.
            question: The natural language question about the data.
            
        Returns:
            str: The agent's analysis and answer in Markdown format.
            
        Raises:
            Exception: If the agent encounters an error during analysis.
            
        Example:
            >>> result = agent.analyze(sales_df, "Show monthly revenue trends")
            >>> print(result)  # Markdown formatted analysis
        """
        try:
            # Create the pandas DataFrame agent with ZERO_SHOT_REACT approach
            # This agent type can handle tasks without needing few-shot examples
            pandas_agent = create_pandas_dataframe_agent(
                llm=self.model,
                df=df,
                verbose=self.verbose,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                allow_dangerous_code=True,  # Required for code execution
                handle_parsing_errors=True,  # Gracefully handle LLM parsing issues
            )
            
            # Construct the full prompt with prefix and suffix
            full_prompt = get_analysis_prompt(question)
            
            # Capture stdout to get the agent's reasoning trace
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                result = pandas_agent.invoke(full_prompt)
            
            # Extract the final output from the agent response
            return result.get("output", str(result))
            
        except Exception as e:
            return f"Analysis error: {e}"


def ask_agent(
    files: List[Any],
    question: str,
    model: Optional[Any] = None
) -> str:
    """
    Analyze uploaded CSV files and answer a question about the data.
    
    This is a convenience function that handles file loading, DataFrame
    concatenation, and agent invocation in one call.
    
    Args:
        files: List of file objects with a .name attribute pointing to CSV paths.
               Typically comes from Gradio's file upload component.
        question: The natural language question to answer about the data.
        model: Optional LLM model to use. If None, uses the global model.
        
    Returns:
        str: The analysis result in Markdown format, or an error message.
        
    Note:
        Multiple CSV files are concatenated into a single DataFrame before
        analysis. Ensure files have compatible schemas for meaningful results.
        
    Example:
        >>> # With Gradio file input
        >>> result = ask_agent(uploaded_files, "What is the total revenue?")
    """
    # Step 1: Load and concatenate all uploaded CSV files
    try:
        dataframes = [pd.read_csv(f.name) for f in files]
        combined_df = pd.concat(dataframes, ignore_index=True)
    except Exception as e:
        return f"Could not read CSV files: {e}"
    
    # Step 2: Create agent and perform analysis
    if model is None:
        return "Error: No LLM model provided. Please configure the model first."
    
    agent = DataFrameAgent(model=model)
    return agent.analyze(combined_df, question)
