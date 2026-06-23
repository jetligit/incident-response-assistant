import anthropic
from dotenv import load_dotenv
import os

load_dotenv() 

def run_agent():
    client = anthropic.Anthropic(os.getenv("CLAUDE_LLM_API_KEY"))

    tools = []

    system_prompt = f"""
        You are an incident response agent that pulls relevant logs and metrics, searches a runbook knowledge base for known fixes,
        reasons through likely root causes, and drafts a remediation plan.

        - Pulls relevant logs and metrics via tool calls
        - Searches a runbook knowledge base (RAG) for known fixes
        - Reasons through likely root causes
        - Drafts a remediation plan and posts it to Slack
        - Optionally executes safe actions (restart a service, clear a queue)
    """

