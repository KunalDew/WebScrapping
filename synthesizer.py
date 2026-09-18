"""
synthesizer.py — Report Generator Module

Takes all approved scraped text and writes a comprehensive,
well-formatted research report answering the original question.

Usage:
    python synthesizer.py
"""

import sys

from config import llm_chat, MAX_TOKENS
from scraper import ScrapedPage

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


SYNTHESIZER_PROMPT = """You are an expert research analyst. Your task is to write a report answering the research question using ONLY the provided source material.

Research Question: {question}

Source Material:
{sources}

Formatting & Structural Guidelines:
1. ADAPTIVE FORMATTING: First, analyze the nature of the Research Question. 
   - If it is a practical, everyday question (like a recipe, a quick how-to, or a simple fact), write a clear, concise, and straightforward guide. Keep it simple and accessible.
   - If it is a complex, technical, or professional topic (like "latest AI architectures" or "market analysis"), write a highly structured, executive-level briefing with an Executive Summary, Deep-Dive Sections, and Markdown Tables.
2. Tone: Match the tone to the subject matter (friendly/accessible for casual topics, objective/academic for professional topics).
3. Synthesis: Combine insights from multiple sources. Highlight consensus and point out any conflicting information between sources.
4. Citations: Every factual claim or specific instruction MUST be cited inline using brackets (e.g., [1], [2]). 
5. References: You MUST include a final "References" section listing every source used, along with its full URL provided in the source block.

Constraint Checklist:
- ONLY use information from the provided sources. Do not hallucinate external facts."""

SYNTHESIZER_DIRECT_PROMPT = """You are an expert AI research analyst. Your task is to write an in-depth, structured research report answering the research question based on your extensive knowledge base.

Research Question: {question}

Formatting & Structural Guidelines:
1. Executive Summary: High-level overview answering the core question.
2. Core Concepts & Architecture: In-depth technical breakdown, methodology, or key components.
3. Comparative Analysis / Real-world Applications: Use Markdown Tables, bullet points, and practical examples.
4. Future Trends & Key Takeaways: Clear actionable insights.
5. Structure: Use clean Markdown headers (##, ###), bold text, and bullet lists for readability.
"""


def _format_sources(pages: list[ScrapedPage]) -> str:
    """Format scraped pages into a numbered source block for the prompt."""
    parts = []
    for i, page in enumerate(pages, 1):
        parts.append(
            f"--- Source [{i}]: {page.title} ---\n"
            f"URL: {page.url}\n"
            f"{page.text}\n"
        )
    return "\n".join(parts)


def synthesize(question: str, pages: list[ScrapedPage]) -> str:
    """
    Generate a research report from approved scraped pages or directly via deep AI reasoning.
    """
    if not pages:
        messages = [
            {"role": "user", "content": SYNTHESIZER_DIRECT_PROMPT.format(question=question)}
        ]
        response = llm_chat(messages, max_tokens=MAX_TOKENS, temperature=0.3)
        return response.strip()
    
    sources_text = _format_sources(pages)
    
    messages = [
        {"role": "user", "content": SYNTHESIZER_PROMPT.format(
            question=question,
            sources=sources_text,
        )}
    ]
    
    response = llm_chat(messages, max_tokens=MAX_TOKENS, temperature=0.3)
    return response.strip()


# ─── Standalone Test ────────────────────────────────────────────
if __name__ == "__main__":
    test_pages = [
        ScrapedPage(
            url="https://example.com/ai-agents",
            title="AI Agents: A Comprehensive Guide",
            text="AI agents are autonomous systems that can perceive their environment, "
                 "make decisions, and take actions to achieve specific goals. Modern AI agents "
                 "use large language models (LLMs) as their reasoning backbone. Key architectures "
                 "include ReAct (Reasoning + Acting), Chain-of-Thought prompting, and tool-augmented "
                 "agents. Recent breakthroughs include multi-agent collaboration frameworks where "
                 "multiple specialized agents work together on complex tasks.",
            success=True,
        ),
        ScrapedPage(
            url="https://example.com/agent-frameworks",
            title="Top AI Agent Frameworks in 2024",
            text="Popular frameworks for building AI agents include LangChain, CrewAI, and AutoGen. "
                 "LangChain provides a modular toolkit for building LLM-powered applications with tools. "
                 "CrewAI specializes in multi-agent orchestration. AutoGen by Microsoft enables "
                 "conversational AI agents that can collaborate on tasks.",
            success=True,
        ),
    ]
    
    question = "What are the latest breakthroughs in AI agent architectures?"
    print(f"📝 Synthesizing report for: \"{question}\"\n")
    
    report = synthesize(question, test_pages)
    # print(report)
