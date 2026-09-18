"""
Shared configuration for the Web Research Agent.
All modules import their LLM client and settings from here.
"""


from openai import OpenAI

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─── LLM Backend ───────────────────────────────────────────────
LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEFAULT_TEMPERATURE = 0.3
MAX_TOKENS = 8192

# ─── Search & Scraping ─────────────────────────────────────────
SEARCH_MAX_RESULTS = 5          # Results per search query
SCRAPE_TIMEOUT = 10             # Seconds per page download
SCRAPE_MAX_CHARS = 5000         # Truncate scraped text to fit context

# ─── Output ────────────────────────────────────────────────────
OUTPUT_DIR = "output"

# ─── Shared LLM Client ─────────────────────────────────────────
# The openai library is API-compatible with DeepSeek's endpoint.
# All modules use this single client instance.
client = OpenAI(
    base_url=LLM_BASE_URL,
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

# Global tracker for total token usage
TOTAL_TOKENS_USED = 0

def llm_chat(messages: list[dict], max_tokens: int = MAX_TOKENS,
             temperature: float = DEFAULT_TEMPERATURE) -> str:
    """
    Send a chat completion request to the local LLM.
    Returns the assistant's response content as a string.
    """
    global TOTAL_TOKENS_USED
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    
    if response.usage:
        TOTAL_TOKENS_USED += response.usage.total_tokens
        
    return response.choices[0].message.content or ""
