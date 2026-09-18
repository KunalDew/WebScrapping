"""
planner.py — Query Generator Module

Takes a research question and asks the LLM to break it down
into 3-4 targeted DuckDuckGo search queries.

Usage:
    python planner.py "What are the latest breakthroughs in AI agents?"
"""

import sys
import re

from config import llm_chat

sys.stdout.reconfigure(encoding='utf-8')


import datetime

PLANNER_PROMPT = """You are an expert research strategist. Your task is to break down a complex research question into exactly 4 highly targeted DuckDuckGo search queries. 

To ensure a comprehensive investigation, your queries should explore different dimensions of the topic, such as:
1. Core definition, primary facts, or main ingredients
2. Expert opinions, analysis, or step-by-step methods
3. Recent developments or news (append {current_year} if recency is implied)
4. Alternative perspectives, variations, or edge cases

Rules:
- Output ONLY the 4 queries, one per line
- Number them 1. 2. 3. 4.
- Use precise, high-signal keywords (3-8 words per query)
- Do NOT include any explanation, conversational filler, or formatting other than the numbered list.

Research Question: {question}"""


def generate_queries(question: str) -> list[str]:
    """
    Use the LLM to generate targeted search queries from a research question.
    
    Args:
        question: The user's research question.
    
    Returns:
        List of 3-4 search query strings.
    """
    messages = [
        {"role": "user", "content": PLANNER_PROMPT.format(
            question=question,
            current_year=datetime.datetime.now().year
        )}
    ]
    
    response = llm_chat(messages, max_tokens=2048, temperature=0.3)
    
    # Parse numbered queries from the response
    queries = []
    for line in response.strip().split("\n"):
        line = line.strip()
        # Match lines starting with a number (e.g., "1. query text" or "1) query text")
        cleaned = re.sub(r"^\d+[\.\)\-]\s*", "", line).strip()
        if cleaned and len(cleaned) > 3:
            queries.append(cleaned)
    
    # Safety: return at least something if parsing fails
    if not queries:
        queries = [question]
    
    return queries[:4]  # Cap at 4 queries


# ─── Standalone Test ────────────────────────────────────────────
if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What are the latest breakthroughs in AI agent architectures?"
    
    print(f"🧠 Planning queries for: \"{question}\"\n")
    
    queries = generate_queries(question)
    
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    
    print(f"\nGenerated {len(queries)} queries.")
