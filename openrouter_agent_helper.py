"""
OpenRouter Agent Helper
Simple utility for calling deployed AI agents

Usage:
    from openrouter_agent_helper import call_agent
    
    response = await call_agent(
        username="wade",
        agent_key="sales",
        message="I'm interested in your marketing services"
    )
"""

import os
import httpx
from typing import Dict, Any, List, Optional
from log_to_jsonbin import get_user


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")


async def call_agent(
    username: str,
    agent_key: str,
    message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> Dict[str, Any]:
    """
    Call an AI agent for a user
    
    Args:
        username: User's username
        agent_key: Agent to call (e.g., "sales", "marketing", "delivery", "finance")
        message: User's message to the agent
        conversation_history: Optional previous messages for context
        temperature: Model temperature (0-2, default 0.7)
        max_tokens: Maximum response length
        
    Returns:
        {
            "ok": True,
            "response": "Agent's response text",
            "agent": "sales",
            "model": "anthropic/claude-3.5-sonnet",
            "tokens_used": 150
        }
    """
    
    if not OPENROUTER_API_KEY:
        return {
            "ok": False,
            "error": "OpenRouter API key not configured"
        }
    
    try:
        # Get user data to load their agent config
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "User not found"}
        
        # Get agent configuration
        actionization = user.get("actionization", {})
        if not actionization.get("deployed"):
            return {"ok": False, "error": "User has no deployed business"}
        
        # Get template type to determine agent role
        template_type = actionization.get("template_type", "marketing")
        
        # Import agent configs
        from openai_agent_deployer import AGENT_CONFIGS
        
        agents_config = AGENT_CONFIGS.get(template_type, {})
        agent_spec = agents_config.get(agent_key)
        
        if not agent_spec:
            return {
                "ok": False,
                "error": f"Agent '{agent_key}' not found for template '{template_type}'"
            }
        
        # Build messages
        messages = [
            {
                "role": "system",
                "content": agent_spec["role"]
            }
        ]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Call OpenRouter
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://aigentsy.com",
                "X-Title": f"AiGentsy - {agent_spec['name']}"
            }
            
            payload = {
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                return {
                    "ok": False,
                    "error": f"OpenRouter API error: {response.status_code}",
                    "details": response.text
                }
            
            result = response.json()
            
            return {
                "ok": True,
                "response": result["choices"][0]["message"]["content"],
                "agent": agent_key,
                "agent_name": agent_spec["name"],
                "model": OPENROUTER_MODEL,
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "finish_reason": result["choices"][0].get("finish_reason")
            }
            
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


async def call_agent_with_tools(
    username: str,
    agent_key: str,
    message: str,
    available_tools: List[str] = None
) -> Dict[str, Any]:
    """
    Call agent with tool-calling capability
    
    This allows agents to call functions like:
    - email_send
    - calendar_book
    - crm_update
    - invoice_generate
    etc.
    
    Args:
        username: User's username
        agent_key: Agent to call
        message: User's message
        available_tools: List of tool names agent can use
        
    Returns:
        {
            "ok": True,
            "response": "Response text",
            "tools_called": [{"tool": "email_send", "args": {...}}]
        }
    """
    
    # For now, just call the regular agent
    # Tool calling would be implemented based on your specific tools
    result = await call_agent(username, agent_key, message)
    
    if result.get("ok"):
        result["tools_called"] = []  # Placeholder for tool calls
    
    return result


# =============================================================
# EXAMPLE USAGE
# =============================================================

async def example_usage():
    """
    Example of how to use the agent helper
    """
    
    # Simple agent call
    response = await call_agent(
        username="wade",
        agent_key="sales",
        message="I'm interested in your marketing services. What do you offer?"
    )
    
    print(f"Agent response: {response['response']}")
    print(f"Tokens used: {response['tokens_used']}")
    
    # Agent call with conversation history
    history = [
        {"role": "user", "content": "Hi, what services do you offer?"},
        {"role": "assistant", "content": "We offer marketing services including SEO, content, and ads."},
    ]
    
    response = await call_agent(
        username="wade",
        agent_key="sales",
        message="How much does SEO cost?",
        conversation_history=history
    )
    
    print(f"Follow-up response: {response['response']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
