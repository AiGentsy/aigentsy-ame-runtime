"""
LLM Configuration for Access Panel
Supports OpenRouter (primary), Gemini, and direct Anthropic

Priority: OpenRouter > Gemini > Anthropic Direct
"""

import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


def get_llm_config(task_type: str = 'general') -> Optional[Dict]:
    """
    Get LLM API configuration based on available credentials

    Task types:
    - selector_healing: Complex code analysis (Claude Sonnet 4)
    - extraction: Data extraction (Claude Sonnet 4)
    - translation: Fast translation (GPT-4 Turbo)
    - scoring: Fast scoring (Gemini Pro or GPT-4)
    - general: Default (Claude Sonnet 4)

    Priority: OpenRouter > Gemini > Anthropic Direct
    """

    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    # Task-specific model routing via OpenRouter
    task_models = {
        'selector_healing': 'anthropic/claude-sonnet-4-20250514',
        'extraction': 'anthropic/claude-sonnet-4-20250514',
        'translation': 'openai/gpt-4-turbo',
        'scoring': 'openai/gpt-4-turbo',
        'general': 'anthropic/claude-sonnet-4-20250514'
    }

    # Priority 1: OpenRouter (gives access to ALL models)
    if openrouter_key:
        model = task_models.get(task_type, task_models['general'])

        logger.debug(f"Using OpenRouter: {model} for {task_type}")

        return {
            'api_key': openrouter_key,
            'base_url': 'https://openrouter.ai/api/v1/chat/completions',
            'model': model,
            'headers': {
                'HTTP-Referer': 'https://aigentsy.com',
                'X-Title': 'AiGentsy Access Panel',
                'Content-Type': 'application/json'
            },
            'provider': 'openrouter'
        }

    # Priority 2: Gemini (for scoring tasks)
    elif gemini_key and task_type in ['scoring', 'translation']:
        logger.debug(f"Using Gemini for {task_type}")

        return {
            'api_key': gemini_key,
            'base_url': 'https://generativelanguage.googleapis.com/v1beta',
            'model': 'gemini-pro',
            'headers': {
                'Content-Type': 'application/json'
            },
            'provider': 'gemini'
        }

    # Priority 3: Direct Anthropic (fallback)
    elif anthropic_key:
        logger.debug(f"Using Anthropic direct for {task_type}")

        return {
            'api_key': anthropic_key,
            'base_url': 'https://api.anthropic.com/v1/messages',
            'model': 'claude-sonnet-4-20250514',
            'headers': {
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            'provider': 'anthropic'
        }

    else:
        logger.warning("No LLM API keys found! Selector healer and LLM extractor disabled.")
        return None


async def call_llm(
    prompt: str,
    task_type: str = 'general',
    max_tokens: int = 2000,
    temperature: float = 0.2
) -> Optional[str]:
    """
    Universal LLM caller
    Handles all providers transparently
    """
    import httpx

    config = get_llm_config(task_type)
    if not config:
        return None

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            if config['provider'] == 'openrouter':
                response = await client.post(
                    config['base_url'],
                    json={
                        'model': config['model'],
                        'messages': [{'role': 'user', 'content': prompt}],
                        'max_tokens': max_tokens,
                        'temperature': temperature
                    },
                    headers={
                        'Authorization': f"Bearer {config['api_key']}",
                        **config['headers']
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.error(f"OpenRouter error: {response.status_code} - {response.text[:200]}")
                    return None

            elif config['provider'] == 'gemini':
                response = await client.post(
                    f"{config['base_url']}/models/{config['model']}:generateContent?key={config['api_key']}",
                    json={
                        'contents': [{
                            'parts': [{'text': prompt}]
                        }],
                        'generationConfig': {
                            'maxOutputTokens': max_tokens,
                            'temperature': temperature
                        }
                    },
                    headers=config['headers']
                )

                if response.status_code == 200:
                    data = response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    logger.error(f"Gemini error: {response.status_code} - {response.text[:200]}")
                    return None

            elif config['provider'] == 'anthropic':
                response = await client.post(
                    config['base_url'],
                    json={
                        'model': config['model'],
                        'max_tokens': max_tokens,
                        'messages': [{'role': 'user', 'content': prompt}],
                        'temperature': temperature
                    },
                    headers={
                        'x-api-key': config['api_key'],
                        **config['headers']
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data['content'][0]['text']
                else:
                    logger.error(f"Anthropic error: {response.status_code} - {response.text[:200]}")
                    return None

    except Exception as e:
        logger.error(f"LLM call failed: {e}")

    return None
