"""
SQL Prompt Templates

This module contains prompt templates for the SQL generation agent.
These prompts guide the LLM in creating and executing SQL queries against
SQLite databases created from user-uploaded CSV files.

Security Note:
    The prompts explicitly prohibit DML statements (INSERT, UPDATE, DELETE, DROP)
    to prevent accidental data modification.
"""

# -----------------------------------------------------------------------------
# SQL Agent Prompts
# -----------------------------------------------------------------------------

SQL_SYSTEM_MESSAGE = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
"""
"""
str: System message template for the SQL agent.

This prompt:
- Defines the agent's role as a SQL database interaction specialist
- Limits query results to prevent overwhelming outputs
- Enforces query validation before execution
- Explicitly prohibits destructive DML operations
- Mandates schema inspection before query generation

Template Variables:
    dialect: The SQL dialect being used (e.g., "SQLite")
    top_k: Maximum number of results to return (default: 5)
"""


SQL_SUFFIX_PROMPT = """
ALWAYS end your answer as follows:

### Final answer

Your query here

--

The answer here
"""
"""
str: Suffix prompt that defines the output format for SQL query results.

This ensures consistent formatting with:
- Clear separation between the generated query and its results
- Markdown-compatible structure for easy rendering
"""


def get_sql_prompt(dialect: str = "SQLite", top_k: int = 5) -> str:
    """
    Generate the SQL system message with configured parameters.
    
    This function formats the SQL system message template with the specified
    database dialect and result limit.
    
    Args:
        dialect: The SQL dialect to use (default: "SQLite").
                 Common options: "SQLite", "PostgreSQL", "MySQL"
        top_k: Maximum number of results to return from queries (default: 5).
        
    Returns:
        str: The formatted system message for the SQL agent.
        
    Example:
        >>> system_msg = get_sql_prompt(dialect="SQLite", top_k=10)
        >>> agent = create_react_agent(llm, tools, prompt=system_msg)
    """
    return SQL_SYSTEM_MESSAGE.format(dialect=dialect, top_k=top_k) + SQL_SUFFIX_PROMPT
