"""
LLM Model Utilities

This module provides helper functions for initializing LLM models
used by the NexDatawork agents.

Supported Models:
    - Azure OpenAI (GPT-4, GPT-3.5-turbo)
    - OpenAI API (GPT-4, GPT-3.5-turbo)
    
Environment Variables Required:
    For Azure:
        - AZURE_OPENAI_ENDPOINT
        - AZURE_OPENAI_API_KEY
    For OpenAI:
        - OPENAI_API_KEY
"""

import os
from typing import Optional, Any

from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


def create_azure_model(
    deployment_name: str = "gpt-4.1",
    api_version: str = "2025-01-01-preview",
    streaming: bool = True,
    temperature: float = 0.0
) -> Any:
    """
    Create an Azure OpenAI chat model instance.
    
    This function initializes an AzureChatOpenAI model with the specified
    configuration. Requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY
    environment variables to be set.
    
    Args:
        deployment_name: The Azure deployment name (default: "gpt-4.1").
        api_version: Azure API version string (default: "2025-01-01-preview").
        streaming: Enable streaming responses (default: True).
        temperature: Model temperature for randomness (default: 0.0 for deterministic).
        
    Returns:
        AzureChatOpenAI: Configured Azure OpenAI model instance.
        
    Raises:
        ImportError: If langchain_openai is not installed.
        ValueError: If required environment variables are not set.
        
    Example:
        >>> model = create_azure_model(deployment_name="gpt-4")
        >>> response = model.invoke("Hello!")
    """
    from langchain_openai import AzureChatOpenAI
    
    # Validate environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable not set")
    
    # Configure callbacks for streaming
    callbacks = [StreamingStdOutCallbackHandler()] if streaming else []
    
    return AzureChatOpenAI(
        openai_api_version=api_version,
        azure_deployment=deployment_name,
        azure_endpoint=endpoint,
        streaming=streaming,
        callbacks=callbacks,
        temperature=temperature,
    )


def create_openai_model(
    model_name: str = "gpt-4-turbo-preview",
    streaming: bool = True,
    temperature: float = 0.0
) -> Any:
    """
    Create an OpenAI chat model instance.
    
    This function initializes a ChatOpenAI model with the specified
    configuration. Requires OPENAI_API_KEY environment variable.
    
    Args:
        model_name: The OpenAI model name (default: "gpt-4-turbo-preview").
        streaming: Enable streaming responses (default: True).
        temperature: Model temperature for randomness (default: 0.0).
        
    Returns:
        ChatOpenAI: Configured OpenAI model instance.
        
    Raises:
        ImportError: If langchain_openai is not installed.
        ValueError: If OPENAI_API_KEY is not set.
        
    Example:
        >>> model = create_openai_model(model_name="gpt-4")
        >>> response = model.invoke("Analyze this data...")
    """
    from langchain_openai import ChatOpenAI
    
    # Validate environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Configure callbacks for streaming
    callbacks = [StreamingStdOutCallbackHandler()] if streaming else []
    
    return ChatOpenAI(
        model=model_name,
        streaming=streaming,
        callbacks=callbacks,
        temperature=temperature,
    )


def get_model(provider: str = "azure", **kwargs) -> Any:
    """
    Factory function to create an LLM model based on provider.
    
    This is a convenience function that delegates to the appropriate
    model creation function based on the provider argument.
    
    Args:
        provider: Either "azure" or "openai" (default: "azure").
        **kwargs: Additional arguments passed to the model creation function.
        
    Returns:
        The configured LLM model instance.
        
    Example:
        >>> model = get_model("openai", model_name="gpt-4")
        >>> model = get_model("azure", deployment_name="gpt-4.1")
    """
    if provider.lower() == "azure":
        return create_azure_model(**kwargs)
    elif provider.lower() == "openai":
        return create_openai_model(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'azure' or 'openai'.")
