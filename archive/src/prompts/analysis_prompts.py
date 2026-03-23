"""
Analysis Prompt Templates

This module contains prompt templates for the DataFrame analysis agent.
These prompts guide the LLM in analyzing pandas DataFrames and generating insights.

The prompts follow a PREFIX + USER_QUESTION + SUFFIX pattern:
- PREFIX: Sets up the analytical approach and methodology
- SUFFIX: Defines the expected output format and structure
"""

# -----------------------------------------------------------------------------
# CSV/DataFrame Analysis Prompts
# -----------------------------------------------------------------------------

CSV_PROMPT_PREFIX = """
Set pandas to show all columns.
Get the column names and infer data types.
Then attempt to answer the question using multiple methods.
Please provide only the Python code required to perform the action, and nothing else.
"""
"""
str: Prefix prompt that instructs the agent on how to approach DataFrame analysis.

This prompt:
- Configures pandas display settings for full visibility
- Directs the agent to inspect column names and data types
- Encourages multi-method validation of results
- Restricts output to executable Python code only
"""


CSV_PROMPT_SUFFIX = """
- Try at least 2 different methods of calculation or filtering.
- Reflect: Do they give the same result?
- After performing all necessary actions and analysis with the dataframe, return the answer in clean **Markdown**, include summary table if needed.
- Include **Execution Recommendation** and **Web Insight** in the final Markdown.
- Always conclude the final Markdown with:

### Final Answer

Your conclusion here.

---

### Explanation

Mention specific columns you used.
Please provide only the Python code required to perform the action, and nothing else until the final Markdown output.
"""
"""
str: Suffix prompt that defines the expected output format for DataFrame analysis.

This prompt:
- Requires multiple validation methods for result accuracy
- Mandates Markdown formatting for the final output
- Includes sections for recommendations and insights
- Ensures explanations reference specific data columns used
"""


def get_analysis_prompt(user_question: str) -> str:
    """
    Construct the full analysis prompt by combining prefix, user question, and suffix.
    
    This function assembles the complete prompt that will be sent to the LLM
    for DataFrame analysis tasks.
    
    Args:
        user_question: The natural language question from the user about their data.
        
    Returns:
        str: The complete prompt string ready for LLM inference.
        
    Example:
        >>> prompt = get_analysis_prompt("What is the average sales per region?")
        >>> agent.invoke(prompt)
    """
    return CSV_PROMPT_PREFIX + user_question + CSV_PROMPT_SUFFIX
