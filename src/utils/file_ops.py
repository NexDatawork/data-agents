"""
File Operations Utilities

This module provides helper functions for file handling operations,
particularly for CSV file processing in the NexDatawork agents.

Functions:
    load_csv_files: Load multiple CSV files into DataFrames
    validate_csv: Validate CSV file structure and content
    get_file_info: Get metadata about uploaded files
"""

import os
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd


def load_csv_files(files: List[Any]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load multiple CSV files and concatenate them into a single DataFrame.
    
    This function reads all provided CSV files and combines them into
    a single DataFrame. Files are concatenated vertically (row-wise).
    
    Args:
        files: List of file objects with a .name attribute pointing to CSV paths.
               Typically comes from Gradio or similar file upload components.
               
    Returns:
        Tuple containing:
            - pd.DataFrame: The concatenated DataFrame
            - List[str]: List of loaded file names
            
    Raises:
        ValueError: If no files are provided or all files fail to load.
        
    Example:
        >>> df, names = load_csv_files(uploaded_files)
        >>> print(f"Loaded {len(names)} files with {len(df)} total rows")
    """
    if not files:
        raise ValueError("No files provided")
    
    dataframes = []
    loaded_names = []
    errors = []
    
    for f in files:
        try:
            # Get file path from file object
            file_path = f.name if hasattr(f, 'name') else str(f)
            
            # Load CSV
            df = pd.read_csv(file_path)
            dataframes.append(df)
            loaded_names.append(os.path.basename(file_path))
            
        except Exception as e:
            errors.append(f"{file_path}: {e}")
    
    if not dataframes:
        raise ValueError(f"Failed to load any files. Errors: {errors}")
    
    # Concatenate all DataFrames
    combined = pd.concat(dataframes, ignore_index=True)
    
    return combined, loaded_names


def validate_csv(file_path: str) -> Dict[str, Any]:
    """
    Validate a CSV file and return information about its structure.
    
    This function checks if a CSV file is valid and returns metadata
    including column types, row count, and any detected issues.
    
    Args:
        file_path: Path to the CSV file to validate.
        
    Returns:
        Dict with keys:
            - valid (bool): Whether the file is a valid CSV
            - rows (int): Number of rows
            - columns (int): Number of columns
            - column_names (List[str]): Column names
            - dtypes (Dict): Column data types
            - missing_values (Dict): Count of missing values per column
            - issues (List[str]): Any detected issues
            
    Example:
        >>> info = validate_csv("sales.csv")
        >>> if info["valid"]:
        ...     print(f"Valid CSV with {info['rows']} rows")
    """
    result = {
        "valid": False,
        "rows": 0,
        "columns": 0,
        "column_names": [],
        "dtypes": {},
        "missing_values": {},
        "issues": []
    }
    
    try:
        # Attempt to load the CSV
        df = pd.read_csv(file_path)
        
        result["valid"] = True
        result["rows"] = len(df)
        result["columns"] = len(df.columns)
        result["column_names"] = list(df.columns)
        result["dtypes"] = df.dtypes.astype(str).to_dict()
        result["missing_values"] = df.isnull().sum().to_dict()
        
        # Check for common issues
        # Duplicate column names
        if len(df.columns) != len(set(df.columns)):
            result["issues"].append("Duplicate column names detected")
        
        # Entirely empty columns
        empty_cols = df.columns[df.isnull().all()].tolist()
        if empty_cols:
            result["issues"].append(f"Empty columns: {empty_cols}")
        
        # High missing value ratio
        high_missing = [
            col for col, count in result["missing_values"].items()
            if count / len(df) > 0.5
        ]
        if high_missing:
            result["issues"].append(f"Columns with >50% missing: {high_missing}")
            
    except Exception as e:
        result["issues"].append(f"Failed to read file: {e}")
    
    return result


def get_file_info(files: List[Any]) -> List[Dict[str, Any]]:
    """
    Get metadata about multiple uploaded files.
    
    Args:
        files: List of file objects with .name attribute.
        
    Returns:
        List of dictionaries containing file metadata:
            - name: File name
            - size_kb: File size in KB
            - validation: Output from validate_csv
            
    Example:
        >>> info = get_file_info(uploaded_files)
        >>> for f in info:
        ...     print(f"{f['name']}: {f['validation']['rows']} rows")
    """
    results = []
    
    for f in files:
        file_path = f.name if hasattr(f, 'name') else str(f)
        
        file_info = {
            "name": os.path.basename(file_path),
            "size_kb": os.path.getsize(file_path) / 1024 if os.path.exists(file_path) else 0,
            "validation": validate_csv(file_path)
        }
        
        results.append(file_info)
    
    return results
