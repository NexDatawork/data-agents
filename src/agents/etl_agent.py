"""
ETL Pipeline Generation Agent

This module implements the ETL (Extract, Transform, Load) agent that
generates data transformation code from natural language instructions.

The agent uses a three-step process:
1. Preview: Inspect the data structure
2. Suggest: Recommend transformations based on data quality
3. Generate: Produce executable Python/pandas code

Example:
    >>> from src.agents import etl_pipeline
    >>> code = etl_pipeline(files)
"""

from typing import List, Optional, Any

import pandas as pd
from langchain.agents import initialize_agent
from langchain.tools import tool


class ETLAgent:
    """
    Agent for generating ETL (Extract, Transform, Load) pipelines.
    
    This agent analyzes data and generates pandas code for common
    data cleaning and transformation tasks.
    
    Attributes:
        model: The LLM model for code generation.
        tools: List of LangChain tools for ETL operations.
        
    Example:
        >>> agent = ETLAgent(model=azure_llm)
        >>> code = agent.generate_pipeline("sales.csv")
    """
    
    def __init__(self, model: Any):
        """
        Initialize the ETL agent with tools.
        
        Args:
            model: The LLM model instance for code generation.
        """
        self.model = model
        self.tools = self._create_tools()
    
    def _create_tools(self) -> List:
        """
        Create the ETL-specific tools for the agent.
        
        Returns:
            List of LangChain tools for data preview, transformation
            suggestion, and code generation.
        """
        model = self.model  # Capture for closure
        
        @tool
        def preview_data(table: str) -> str:
            """
            Read and preview a CSV table.
            
            Returns the first few rows and column information
            to help understand the data structure.
            """
            df = pd.read_csv(table)
            info = f"Shape: {df.shape}\n"
            info += f"Columns: {list(df.columns)}\n"
            info += f"Dtypes:\n{df.dtypes}\n\n"
            info += f"Head:\n{df.head()}"
            return info
        
        @tool
        def suggest_transformation(column_summary: str) -> str:
            """
            Suggest ETL transformations based on column summary.
            
            Analyzes the column information and recommends
            appropriate data cleaning steps.
            """
            prompt = f"""
            You are a data engineer assistant. Based on the following column summary, 
            suggest simple, short ETL transformation steps.
            Output format: each suggestion on a new line, without explanations or markdown.
            Example:
            Remove $ from revenue and cast to float
            Convert date column to datetime format
            Fill missing values in quantity with 0

            Column summary:
            {column_summary}
            """
            return model.predict(prompt).strip()
        
        @tool
        def generate_python_code(transform_description: str) -> str:
            """
            Generate pandas code from transformation description.
            
            Converts natural language transformation steps into
            executable Python/pandas code.
            """
            prompt = f"""
            You are a data engineer. Write pandas code to apply the following 
            ETL transformation to a dataframe called 'df'.

            Transformations:
            {transform_description}

            Only return pandas code. No explanation, no markdown.
            """
            return model.predict(prompt).strip()
        
        return [preview_data, suggest_transformation, generate_python_code]
    
    def generate_pipeline(self, table_path: str) -> str:
        """
        Generate an ETL pipeline for a given table.
        
        This method creates a LangChain agent that:
        1. Previews the table structure
        2. Suggests appropriate transformations
        3. Generates Python code for the transformations
        
        Args:
            table_path: Path to the CSV file to process.
            
        Returns:
            str: Generated Python code for the ETL pipeline.
            
        Example:
            >>> code = agent.generate_pipeline("raw_sales.csv")
            >>> exec(code)  # Apply transformations
        """
        try:
            # Create the agent with ETL tools
            agent = initialize_agent(
                self.tools,
                self.model,
                agent='zero-shot-react-description',
                verbose=True
            )
            
            # Construct the input prompt for pipeline generation
            input_prompt = f"""
            Preview the table {table_path} and generate Python code to read 
            the table, clean it, and finally write the dataframe into a table 
            called 'Cleaned_{table_path.replace('.csv', '')}'. 
            Do not stop the Python session.
            """
            
            # Run the agent using the newer invoke API
            response = agent.invoke({
                "input": input_prompt,
                "chat_history": [],
                "handle_parsing_errors": True
            })
            
            # Extract the textual output and clean it up (remove markdown code blocks if present)
            output_text = response.get("output", "") if isinstance(response, dict) else str(response)
            code = output_text.strip('`').replace('python', '').strip()
            return code
            
        except Exception as e:
            return f"ETL pipeline error: {e}"


def etl_pipeline(
    dataframe: List[Any],
    model: Optional[Any] = None
) -> str:
    """
    Generate an ETL pipeline for uploaded data files.
    
    This is a convenience function that wraps the ETLAgent class
    for simple pipeline generation tasks.
    
    Args:
        dataframe: List containing file path(s) to process.
                   Uses the first file in the list.
        model: Optional LLM model. If None, uses global model.
        
    Returns:
        str: Generated Python code for data transformation.
        
    Example:
        >>> code = etl_pipeline(["sales.csv"], model)
        >>> print(code)
    """
    if model is None:
        return "Error: No LLM model provided."
    
    if not dataframe:
        return "Error: No files provided."
    
    # Get the first file path
    table_name = dataframe[0] if isinstance(dataframe[0], str) else dataframe[0].name
    
    agent = ETLAgent(model=model)
    return agent.generate_pipeline(table_name)
