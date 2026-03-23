"""
Web Scraping Prompt Templates

This module contains prompt templates for the AI-powered web scraping agent.
These prompts guide the LLM in extracting structured data from web pages
using the SmartScraperTool.

Output Format:
    All scraped data is converted to pandas DataFrames with clean,
    string/numeric values only (no nested structures).
"""

# -----------------------------------------------------------------------------
# Web Scraping Agent Prompts
# -----------------------------------------------------------------------------

SCRAPING_PROMPT_PREFIX = """
ROLE: Expert Data Scraper
MISSION: Extract precise online data using systematic keyword analysis

THINKING PROCESS:
1. Keyword Analysis: Identify primary entities (X, Y) and quantifiers (n, m)
2. Query Strategy: Formulate targeted search queries for each entity
3. Data Extraction: Scrape exact quantities specified
4. Validation: Verify results match request parameters

EXAMPLE:
User: "List first 5 startups and 3 investors in AI"
Keywords: ["startups:5", "investors:3", "AI"]
Action: Search "AI startups" -> extract 5 instances -> Search "AI investors" -> extract 3 instances

WORKFLOW:
- Print identified keywords with quantities
- Execute sequential searches per keyword group
- Collect exactly specified instances
- Present structured results

READY FOR QUERY.
"""
"""
str: Prefix prompt that defines the scraping agent's role and methodology.

This prompt:
- Establishes the agent as an expert data scraper
- Defines a systematic keyword analysis approach
- Provides a concrete example of the expected workflow
- Ensures precise quantity extraction matching user requests
"""


SCRAPING_PROMPT_SUFFIX = """
ROLE: Data Extraction Agent
MISSION: Structure all scraped data as valid pandas DataFrames

OUTPUT REQUIREMENTS:
- Format: pandas DataFrame
- Columns: 1-2 word descriptive names
- Content: Only strings or numerical values (no lists/dicts, no nested structures)
- Validation: Must pass pd.DataFrame access tests

VALIDATION CHECKLIST:
- Each column contains only strings or numerics
- No nested structures (lists/dicts) in cells
- Column names are descriptive and concise
- DataFrame is accessible via standard indexing
- All columns MUST BE OF THE SAME LENGTH

EXAMPLE OUTPUT:
pd.DataFrame({
    'Company': ['Startup A', 'Startup B'],
    'Funding': [5000000, 7500000],
    'Industry': ['Artificial Intelligence', 'Artificial Intelligence']
})
"""
"""
str: Suffix prompt that defines the required output format for scraped data.

This prompt:
- Mandates pandas DataFrame output format
- Requires clean, flat data structures (no nesting)
- Provides validation criteria for data quality
- Includes a concrete example of expected output format

Note:
    The validation checklist ensures data compatibility with downstream
    processing and prevents common DataFrame construction errors.
"""


def get_scraping_prompt(user_query: str) -> str:
    """
    Construct the full web scraping prompt for a given user query.
    
    This function assembles the complete prompt by combining the prefix,
    user's data extraction request, and the suffix format requirements.
    
    Args:
        user_query: The natural language description of data to scrape.
                    Example: "Find the top 10 AI companies and their funding amounts"
        
    Returns:
        str: The complete prompt string ready for the scraping agent.
        
    Example:
        >>> prompt = get_scraping_prompt("List 5 popular Python libraries for ML")
        >>> response = agent.run(prompt)
    """
    return SCRAPING_PROMPT_PREFIX + user_query + SCRAPING_PROMPT_SUFFIX
