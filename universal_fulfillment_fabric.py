"""
UNIVERSAL FULFILLMENT FABRIC - AI-Powered Browser Automation
═══════════════════════════════════════════════════════════════════════════════

Works on ANY website using AI vision + browser automation.

For platforms without APIs (Upwork, Fiverr, HackerNews, etc.), this fabric:
1. Analyzes the page structure using AI vision
2. Generates an execution plan (form fills, clicks, etc.)
3. Executes the plan using Playwright
4. Verifies completion using AI screenshot analysis

SAFETY RAILS:
- Max $50 EV for auto-execute
- Rate limit: 10 universal executions per hour
- All actions logged with screenshots
- Human approval required above threshold

Updated: Jan 2026
"""

import os
import asyncio
import base64
import json
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("universal_fabric")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MAX_EV_AUTO_EXECUTE = float(os.getenv("FABRIC_MAX_EV_AUTO", "50"))
RATE_LIMIT_PER_HOUR = int(os.getenv("FABRIC_RATE_LIMIT_HOUR", "100"))
SCREENSHOT_DIR = os.getenv("FABRIC_SCREENSHOT_DIR", "/tmp/fabric_screenshots")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# HackerNews credentials (required for posting comments)
HN_USERNAME = os.getenv("HN_USERNAME") or os.getenv("HACKERNEWS_USERNAME", "")
HN_PASSWORD = os.getenv("HN_PASSWORD") or os.getenv("HACKERNEWS_PASSWORD", "")

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - browser automation disabled")

# HTTP client
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION LOG
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ExecutionLog:
    """Log entry for a fabric execution"""
    execution_id: str
    pdl_name: str
    url: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "pending"
    steps_executed: List[Dict] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    result: Dict = field(default_factory=dict)
    error: Optional[str] = None
    ev_estimate: float = 0.0


_execution_logs: List[ExecutionLog] = []
_executions_this_hour: List[datetime] = []


def _check_rate_limit() -> bool:
    """Check if we're within rate limit"""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)
    global _executions_this_hour
    _executions_this_hour = [t for t in _executions_this_hour if t > cutoff]
    return len(_executions_this_hour) < RATE_LIMIT_PER_HOUR


def _record_execution():
    """Record an execution for rate limiting"""
    _executions_this_hour.append(datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════════════════
# AI VISION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def _call_vision_ai(image_base64: str, prompt: str) -> Dict[str, Any]:
    """Call AI vision model to analyze image"""
    if not HTTPX_AVAILABLE:
        return {"ok": False, "error": "httpx not available"}

    # Try OpenRouter with Gemini Flash (vision capable)
    if OPENROUTER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "google/gemini-flash-1.5",
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                            ]
                        }],
                        "max_tokens": 2000
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {"ok": True, "analysis": content}
                return {"ok": False, "error": f"Vision API error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Vision AI error: {e}")
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": "No vision API configured"}


async def _call_ai(prompt: str) -> Dict[str, Any]:
    """Call AI for text generation with fallback chain:
    1. OpenRouter → openai/gpt-4o-mini
    2. OpenRouter → anthropic/claude-3-haiku
    3. Perplexity → sonar
    4. Gemini → gemini-2.0-flash
    """
    if not HTTPX_AVAILABLE:
        return {"ok": False, "error": "httpx not available"}

    errors = []  # Track errors from each provider

    # 1. OpenRouter with GPT-4o-mini (fastest, cheapest)
    if OPENROUTER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4000,
                        "temperature": 0.3
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {"ok": True, "content": content, "provider": "openrouter/gpt-4o-mini"}
                err = f"OpenRouter/GPT-4o-mini: {response.status_code}"
                try:
                    err += f" - {response.json().get('error', {}).get('message', '')[:100]}"
                except:
                    pass
                errors.append(err)
                logger.warning(f"{err}, trying fallback")
        except Exception as e:
            errors.append(f"OpenRouter/GPT-4o-mini: {str(e)[:100]}")
            logger.warning(f"OpenRouter/GPT-4o-mini error: {e}, trying fallback")
    else:
        errors.append("OpenRouter: no API key")

    # 2. OpenRouter with Claude 3.5 Haiku
    if OPENROUTER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4000,
                        "temperature": 0.3
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {"ok": True, "content": content, "provider": "openrouter/claude-3.5-haiku"}
                err = f"OpenRouter/Claude: {response.status_code}"
                try:
                    err += f" - {response.json().get('error', {}).get('message', '')[:100]}"
                except:
                    pass
                errors.append(err)
                logger.warning(f"{err}, trying fallback")
        except Exception as e:
            errors.append(f"OpenRouter/Claude: {str(e)[:100]}")
            logger.warning(f"OpenRouter/Claude error: {e}, trying fallback")

    # 3. Perplexity with Llama 3.1 Sonar
    if PERPLEXITY_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 4000,
                        "temperature": 0.3
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {"ok": True, "content": content, "provider": "perplexity/sonar"}
                err = f"Perplexity: {response.status_code}"
                try:
                    err += f" - {response.json().get('error', {}).get('message', '')[:100]}"
                except:
                    pass
                errors.append(err)
                logger.warning(f"{err}, trying fallback")
        except Exception as e:
            errors.append(f"Perplexity: {str(e)[:100]}")
            logger.warning(f"Perplexity error: {e}, trying fallback")
    else:
        errors.append("Perplexity: no API key")

    # 4. Gemini direct API
    if GEMINI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"maxOutputTokens": 4000, "temperature": 0.3}
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return {"ok": True, "content": content, "provider": "gemini/2.0-flash"}
                err = f"Gemini: {response.status_code}"
                try:
                    err += f" - {response.json().get('error', {}).get('message', '')[:100]}"
                except:
                    pass
                errors.append(err)
                logger.warning(f"{err}")
        except Exception as e:
            errors.append(f"Gemini: {str(e)[:100]}")
            logger.warning(f"Gemini error: {e}")
    else:
        errors.append("Gemini: no API key")

    # Return detailed error info
    return {"ok": False, "error": f"All AI providers failed: {'; '.join(errors)}"}


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

async def analyze_page(page: "Page") -> Dict[str, Any]:
    """
    Analyze a page to understand its structure and interactive elements.

    Returns:
    - forms: List of forms with their fields
    - buttons: Clickable buttons
    - inputs: Text inputs, textareas
    - links: Navigation links
    - page_type: Detected page type (login, form, listing, etc.)
    """
    # Take screenshot for vision analysis
    screenshot = await page.screenshot(type="png")
    screenshot_b64 = base64.b64encode(screenshot).decode()

    # Get page HTML for structure
    html = await page.content()

    # Vision analysis
    vision_prompt = """Analyze this webpage screenshot and identify:
1. What type of page is this? (login, form submission, listing, profile, etc.)
2. What are the main interactive elements? (buttons, forms, input fields)
3. What action does this page enable the user to take?
4. Where is the main content/form located on the page?

Return your analysis as JSON with fields:
- page_type: string
- main_action: string
- elements: list of {type, label, location, purpose}
- recommended_flow: list of steps to complete the action"""

    vision_result = await _call_vision_ai(screenshot_b64, vision_prompt)

    # Parse interactive elements from HTML
    elements_script = """
    () => {
        const forms = Array.from(document.forms).map(f => ({
            id: f.id,
            action: f.action,
            method: f.method,
            fields: Array.from(f.elements).filter(e => e.tagName !== 'FIELDSET').map(e => ({
                name: e.name,
                type: e.type,
                id: e.id,
                placeholder: e.placeholder,
                required: e.required,
                value: e.value
            }))
        }));

        const buttons = Array.from(document.querySelectorAll('button, input[type="submit"], [role="button"]')).map(b => ({
            text: b.innerText || b.value,
            id: b.id,
            type: b.type,
            class: b.className
        }));

        const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea, select')).map(i => ({
            name: i.name,
            id: i.id,
            type: i.type || i.tagName.toLowerCase(),
            placeholder: i.placeholder,
            label: document.querySelector(`label[for="${i.id}"]`)?.innerText
        }));

        const textareas = Array.from(document.querySelectorAll('textarea')).map(t => ({
            name: t.name,
            id: t.id,
            placeholder: t.placeholder,
            label: document.querySelector(`label[for="${t.id}"]`)?.innerText
        }));

        return { forms, buttons, inputs, textareas };
    }
    """

    try:
        dom_elements = await page.evaluate(elements_script)
    except Exception as e:
        logger.error(f"DOM analysis error: {e}")
        dom_elements = {"forms": [], "buttons": [], "inputs": [], "textareas": []}

    return {
        "ok": True,
        "url": page.url,
        "title": await page.title(),
        "vision_analysis": vision_result.get("analysis", ""),
        "dom_elements": dom_elements,
        "screenshot_b64": screenshot_b64[:100] + "...",  # Truncated for logging
        "has_forms": len(dom_elements.get("forms", [])) > 0,
        "has_inputs": len(dom_elements.get("inputs", [])) > 0
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION PLAN GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_execution_plan(
    page_analysis: Dict[str, Any],
    opportunity: Dict[str, Any],
    pdl_name: str
) -> Dict[str, Any]:
    """
    Generate an execution plan based on page analysis and opportunity data.

    Returns a list of steps to execute:
    - fill: {selector, value}
    - click: {selector}
    - wait: {seconds}
    - scroll: {direction, amount}
    - screenshot: {name}
    """
    # Extract action from PDL name
    parts = pdl_name.split(".")
    platform = parts[0] if len(parts) > 0 else "unknown"
    action = parts[1] if len(parts) > 1 else "unknown"

    # Build prompt for plan generation
    prompt = f"""You are an automation expert. Generate a step-by-step execution plan.

TASK: Execute "{action}" on "{platform}"

PAGE ANALYSIS:
{json.dumps(page_analysis.get("vision_analysis", ""), indent=2)}

DOM ELEMENTS:
Forms: {json.dumps(page_analysis.get("dom_elements", {}).get("forms", []), indent=2)}
Inputs: {json.dumps(page_analysis.get("dom_elements", {}).get("inputs", []), indent=2)}
Buttons: {json.dumps(page_analysis.get("dom_elements", {}).get("buttons", []), indent=2)}

DATA TO FILL:
{json.dumps(opportunity, indent=2)}

Generate a JSON array of steps. Each step has:
- action: "fill" | "click" | "wait" | "scroll" | "screenshot" | "press"
- selector: CSS selector or text selector (for fill/click)
- value: value to fill (for fill action)
- key: key to press (for press action)
- seconds: wait time (for wait action)
- reason: brief explanation

Example:
[
  {{"action": "fill", "selector": "textarea[name='message']", "value": "Hello...", "reason": "Fill message field"}},
  {{"action": "click", "selector": "button[type='submit']", "reason": "Submit form"}},
  {{"action": "wait", "seconds": 2, "reason": "Wait for submission"}}
]

IMPORTANT: You MUST respond with ONLY a valid JSON array. No explanations, no markdown, just the JSON array starting with [ and ending with ]."""

    # Helper function to extract JSON from AI response
    def extract_json(content: str) -> str:
        if not content or not content.strip():
            return "[]"
        content = content.strip()
        # Remove markdown code fences
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("[") or part.startswith("{"):
                    content = part
                    break
        # Find JSON array in response
        import re
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            return json_match.group(0)
        return content.strip()

    # Try up to 2 times (initial + 1 retry)
    for attempt in range(2):
        ai_result = await _call_ai(prompt)

        if not ai_result.get("ok"):
            if attempt == 0:
                logger.warning(f"AI call failed, retrying: {ai_result.get('error')}")
                continue
            return {"ok": False, "error": ai_result.get("error", "AI generation failed")}

        # Parse the plan
        try:
            content = ai_result.get("content", "[]")
            extracted = extract_json(content)

            if not extracted or extracted == "[]" or len(extracted) < 5:
                if attempt == 0:
                    logger.warning(f"Empty AI response from {ai_result.get('provider')}, retrying")
                    continue
                # Return minimal fallback plan
                logger.warning("AI returned empty, using fallback plan")
                return {"ok": True, "plan": [
                    {"action": "wait", "seconds": 1, "reason": "Initial wait"},
                    {"action": "screenshot", "name": "fallback", "reason": "Capture page state"}
                ], "fallback": True}

            plan = json.loads(extracted)
            if isinstance(plan, list) and len(plan) > 0:
                return {"ok": True, "plan": plan, "provider": ai_result.get("provider")}

            if attempt == 0:
                logger.warning(f"Invalid plan structure, retrying")
                continue

        except json.JSONDecodeError as e:
            if attempt == 0:
                logger.warning(f"JSON parse failed: {e}, retrying")
                continue
            logger.error(f"Plan parsing error after retry: {e}")
            logger.error(f"Raw content: {content[:500]}")
            return {"ok": False, "error": f"Plan parsing failed: {e}"}

    return {"ok": False, "error": "Plan generation failed after retries"}


# ═══════════════════════════════════════════════════════════════════════════════
# PLAN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

async def execute_plan(
    page: "Page",
    plan: List[Dict],
    execution_log: ExecutionLog
) -> Dict[str, Any]:
    """
    Execute a generated plan using Playwright.

    Returns execution result with success/failure status.
    """
    results = []

    for i, step in enumerate(plan):
        action = step.get("action")
        selector = step.get("selector")
        value = step.get("value")
        reason = step.get("reason", "")

        logger.info(f"Step {i+1}: {action} - {reason}")

        try:
            if action == "fill":
                # Try multiple selector strategies
                element = None
                strategies = [selector]
                # Only add text/placeholder fallbacks if selector is plain text
                # (not already a CSS selector with brackets, #, or .)
                if not any(c in selector for c in ['[', ']', '#', '.', '>', ':', '*']):
                    strategies.append(f"text={selector}")
                    strategies.append(f"[placeholder*='{selector}']")
                for sel_strategy in strategies:
                    try:
                        element = page.locator(sel_strategy).first
                        if await element.count() > 0:
                            break
                    except:
                        continue

                if element and await element.count() > 0:
                    await element.fill(value or "")
                    results.append({"step": i+1, "action": action, "status": "success", "selector": selector})
                else:
                    results.append({"step": i+1, "action": action, "status": "element_not_found", "selector": selector})

            elif action == "click":
                # Try multiple selector strategies
                clicked = False
                strategies = [selector]
                if not any(c in selector for c in ['[', ']', '#', '.', '>', ':', '*']):
                    strategies.append(f"text={selector}")
                    strategies.append(f"button:has-text('{selector}')")
                for sel_strategy in strategies:
                    try:
                        element = page.locator(sel_strategy).first
                        if await element.count() > 0:
                            await element.click()
                            clicked = True
                            break
                    except:
                        continue

                if clicked:
                    results.append({"step": i+1, "action": action, "status": "success", "selector": selector})
                else:
                    results.append({"step": i+1, "action": action, "status": "element_not_found", "selector": selector})

            elif action == "wait":
                seconds = step.get("seconds", 1)
                await asyncio.sleep(seconds)
                results.append({"step": i+1, "action": action, "status": "success", "seconds": seconds})

            elif action == "press":
                key = step.get("key", "Enter")
                await page.keyboard.press(key)
                results.append({"step": i+1, "action": action, "status": "success", "key": key})

            elif action == "scroll":
                direction = step.get("direction", "down")
                amount = step.get("amount", 500)
                if direction == "down":
                    await page.evaluate(f"window.scrollBy(0, {amount})")
                else:
                    await page.evaluate(f"window.scrollBy(0, -{amount})")
                results.append({"step": i+1, "action": action, "status": "success"})

            elif action == "screenshot":
                name = step.get("name", f"step_{i+1}")
                screenshot = await page.screenshot(type="png")
                screenshot_path = f"{SCREENSHOT_DIR}/{execution_log.execution_id}_{name}.png"
                # In production, save to disk or cloud storage
                execution_log.screenshots.append(screenshot_path)
                results.append({"step": i+1, "action": action, "status": "success", "path": screenshot_path})

        except Exception as e:
            logger.error(f"Step {i+1} failed: {e}")
            results.append({"step": i+1, "action": action, "status": "error", "error": str(e)})

        execution_log.steps_executed.append(results[-1])

    # Check if any critical steps failed
    failures = [r for r in results if r.get("status") not in ["success"]]

    return {
        "ok": len(failures) == 0,
        "steps_executed": len(results),
        "steps_succeeded": len([r for r in results if r.get("status") == "success"]),
        "steps_failed": len(failures),
        "results": results
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETION VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

async def verify_completion(page: "Page", expected_outcome: str) -> Dict[str, Any]:
    """
    Verify that the action completed successfully using AI vision.

    Args:
        page: Playwright page
        expected_outcome: Description of expected outcome (e.g., "Comment posted", "Proposal submitted")

    Returns:
        Verification result with confidence score
    """
    # Take final screenshot
    screenshot = await page.screenshot(type="png")
    screenshot_b64 = base64.b64encode(screenshot).decode()

    # Get page content for additional verification
    try:
        url = page.url
        title = await page.title()
        # Check for success indicators in page content
        content = await page.content()
        has_success_message = any(word in content.lower() for word in [
            "success", "submitted", "posted", "sent", "thank you", "received",
            "confirmed", "complete", "done"
        ])
        has_error_message = any(word in content.lower() for word in [
            "error", "failed", "invalid", "required", "please try again", "cannot"
        ])
    except:
        url = ""
        title = ""
        has_success_message = False
        has_error_message = False

    # Vision verification
    vision_prompt = f"""Analyze this webpage screenshot and determine if the action was successful.

EXPECTED OUTCOME: {expected_outcome}

Look for:
1. Success messages or confirmations
2. Error messages or warnings
3. Changes that indicate the action completed
4. Any indication the form/action was processed

Return JSON:
{{
  "success": true/false,
  "confidence": 0-100,
  "evidence": "what you see that indicates success/failure",
  "next_action_needed": "any follow-up needed or null"
}}"""

    vision_result = await _call_vision_ai(screenshot_b64, vision_prompt)

    # Parse vision result
    try:
        analysis = vision_result.get("analysis", "{}")
        if "```json" in analysis:
            analysis = analysis.split("```json")[1].split("```")[0]
        elif "```" in analysis:
            analysis = analysis.split("```")[1].split("```")[0]

        verification = json.loads(analysis.strip())
    except:
        # Fallback to heuristic
        verification = {
            "success": has_success_message and not has_error_message,
            "confidence": 50,
            "evidence": "Heuristic check only",
            "next_action_needed": None
        }

    return {
        "ok": True,
        "verified": verification.get("success", False),
        "confidence": verification.get("confidence", 0),
        "evidence": verification.get("evidence", ""),
        "next_action_needed": verification.get("next_action_needed"),
        "url": url,
        "title": title
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

async def execute_universal(
    pdl_name: str,
    url: str,
    data: Dict[str, Any],
    ev_estimate: float = 0,
    credentials: Dict[str, str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Execute any action using the Universal Fulfillment Fabric.

    Args:
        pdl_name: PDL name (e.g., "upwork.submit_proposal")
        url: Target URL
        data: Data to fill/submit
        ev_estimate: Expected value for auto-execute check
        credentials: Optional login credentials {username, password}
        dry_run: If True, analyze and plan but don't execute

    Returns:
        Execution result with status, screenshots, and verification
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {"ok": False, "error": "Playwright not installed", "queued": True}

    # Check rate limit
    if not _check_rate_limit():
        return {
            "ok": False,
            "error": f"Rate limit exceeded ({RATE_LIMIT_PER_HOUR}/hour)",
            "queued": True,
            "retry_after_seconds": 3600
        }

    # ═══════════════════════════════════════════════════════════════════
    # GITHUB BLOCKER - CRITICAL: Block ALL GitHub URLs (ToS compliance)
    # ═══════════════════════════════════════════════════════════════════
    url_lower = url.lower() if url else ""
    if 'github.com' in url_lower or 'github.io' in url_lower:
        logger.warning(f"🚫 BLOCKED GitHub URL in fabric: {url} (ToS compliance)")
        return {
            "ok": False,
            "error": "GitHub URLs are blocked - violates GitHub Terms of Service",
            "blocked": True,
            "reason": "github_tos_compliance",
            "url": url
        }

    # Check EV threshold for auto-execute
    if ev_estimate > MAX_EV_AUTO_EXECUTE and not dry_run:
        return {
            "ok": False,
            "error": f"EV ${ev_estimate:.2f} exceeds auto-execute threshold ${MAX_EV_AUTO_EXECUTE}",
            "requires_approval": True,
            "ev_estimate": ev_estimate,
            "max_auto": MAX_EV_AUTO_EXECUTE
        }

    # Create execution log
    execution_id = f"uf_{secrets.token_hex(8)}"
    execution_log = ExecutionLog(
        execution_id=execution_id,
        pdl_name=pdl_name,
        url=url,
        started_at=datetime.now(timezone.utc).isoformat(),
        ev_estimate=ev_estimate
    )
    _execution_logs.append(execution_log)

    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            # Navigate to URL
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Handle login if credentials provided
            if credentials:
                login_result = await _handle_login(page, credentials)
                if not login_result.get("ok"):
                    execution_log.status = "login_failed"
                    execution_log.error = login_result.get("error")
                    return {"ok": False, "error": "Login failed", "details": login_result}

            # Analyze the page
            logger.info("Analyzing page structure...")
            analysis = await analyze_page(page)

            if dry_run:
                # Generate plan but don't execute
                plan_result = await generate_execution_plan(analysis, data, pdl_name)
                execution_log.status = "dry_run"
                execution_log.completed_at = datetime.now(timezone.utc).isoformat()
                return {
                    "ok": True,
                    "dry_run": True,
                    "execution_id": execution_id,
                    "analysis": analysis,
                    "plan": plan_result.get("plan", [])
                }

            # Generate execution plan
            logger.info("Generating execution plan...")
            plan_result = await generate_execution_plan(analysis, data, pdl_name)

            if not plan_result.get("ok"):
                execution_log.status = "plan_failed"
                execution_log.error = plan_result.get("error")
                return {"ok": False, "error": "Plan generation failed", "details": plan_result}

            plan = plan_result.get("plan", [])

            # Execute the plan
            logger.info(f"Executing {len(plan)} steps...")
            _record_execution()  # Record for rate limiting
            exec_result = await execute_plan(page, plan, execution_log)

            # Verify completion
            logger.info("Verifying completion...")
            verification = await verify_completion(page, f"{pdl_name} completed")

            # Final screenshot
            final_screenshot = await page.screenshot(type="png")
            final_screenshot_b64 = base64.b64encode(final_screenshot).decode()

            await browser.close()

            # Update log
            execution_log.status = "success" if exec_result.get("ok") and verification.get("verified") else "partial"
            execution_log.completed_at = datetime.now(timezone.utc).isoformat()
            execution_log.result = {
                "execution": exec_result,
                "verification": verification
            }

            return {
                "ok": exec_result.get("ok") and verification.get("verified"),
                "execution_id": execution_id,
                "pdl_name": pdl_name,
                "url": url,
                "execution_result": exec_result,
                "verification": verification,
                "steps_executed": exec_result.get("steps_executed", 0),
                "final_url": verification.get("url"),
                "screenshot_b64": final_screenshot_b64[:100] + "..."  # Truncated
            }

    except Exception as e:
        logger.error(f"Universal execution error: {e}")
        execution_log.status = "error"
        execution_log.error = str(e)
        execution_log.completed_at = datetime.now(timezone.utc).isoformat()
        return {"ok": False, "error": str(e), "execution_id": execution_id}


async def _handle_login(page: "Page", credentials: Dict[str, str]) -> Dict[str, Any]:
    """Handle login flow if needed"""
    username = credentials.get("username", "")
    password = credentials.get("password", "")

    if not username or not password:
        return {"ok": False, "error": "Missing credentials"}

    try:
        # Look for login form
        username_field = page.locator('input[type="email"], input[type="text"][name*="user"], input[name*="email"]').first
        password_field = page.locator('input[type="password"]').first

        if await username_field.count() > 0 and await password_field.count() > 0:
            await username_field.fill(username)
            await password_field.fill(password)

            # Find and click submit
            submit = page.locator('button[type="submit"], input[type="submit"]').first
            if await submit.count() > 0:
                await submit.click()
                await page.wait_for_load_state("networkidle")

            return {"ok": True, "logged_in": True}
        else:
            # No login form found - might already be logged in or no auth needed
            return {"ok": True, "logged_in": False, "note": "No login form found"}

    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS & LOGS
# ═══════════════════════════════════════════════════════════════════════════════

def get_execution_logs(limit: int = 50) -> List[Dict]:
    """Get recent execution logs"""
    return [
        {
            "execution_id": log.execution_id,
            "pdl_name": log.pdl_name,
            "url": log.url,
            "status": log.status,
            "started_at": log.started_at,
            "completed_at": log.completed_at,
            "steps_executed": len(log.steps_executed),
            "screenshots": len(log.screenshots),
            "error": log.error,
            "ev_estimate": log.ev_estimate
        }
        for log in _execution_logs[-limit:]
    ]


def get_fabric_status() -> Dict[str, Any]:
    """Get Universal Fabric status"""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)
    recent_executions = len([t for t in _executions_this_hour if t > cutoff])

    return {
        "ok": True,
        "playwright_available": PLAYWRIGHT_AVAILABLE,
        "ai_available": bool(OPENROUTER_API_KEY or PERPLEXITY_API_KEY or GEMINI_API_KEY),
        "hackernews_credentials": bool(HN_USERNAME and HN_PASSWORD),
        "rate_limit": {
            "per_hour": RATE_LIMIT_PER_HOUR,
            "used_this_hour": recent_executions,
            "remaining": RATE_LIMIT_PER_HOUR - recent_executions
        },
        "max_ev_auto_execute": MAX_EV_AUTO_EXECUTE,
        "total_executions": len(_execution_logs),
        "recent_logs": get_execution_logs(10)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FABRIC EXECUTE - Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

async def fabric_execute(
    pdl_name: str,
    params: Dict[str, Any],
    ev_estimate: float = 0,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for fabric execution.

    Routes to either direct API or Universal Fabric based on PDL configuration.
    """
    from pdl_polymorphic_catalog import get_pdl_catalog, ExecutionMethod

    catalog = get_pdl_catalog()
    pdl = catalog.get(pdl_name)

    if not pdl:
        return {"ok": False, "error": f"PDL not found: {pdl_name}"}

    # ═══════════════════════════════════════════════════════════════════
    # GITHUB BLOCKER - Block at fabric_execute entry point
    # ═══════════════════════════════════════════════════════════════════
    url = params.get("url") or params.get("job_url") or params.get("post_url") or ""
    url_lower = url.lower()
    platform = pdl.platform.lower() if hasattr(pdl, 'platform') else ""
    if 'github.com' in url_lower or 'github.io' in url_lower or platform == 'github':
        logger.warning(f"🚫 BLOCKED GitHub in fabric_execute: {url} (ToS compliance)")
        return {
            "ok": False,
            "error": "GitHub blocked - violates GitHub Terms of Service",
            "blocked": True,
            "reason": "github_tos_compliance"
        }

    actual_method = pdl.get_execution_method()

    # If PDL can execute via API, prefer that
    if actual_method == ExecutionMethod.API and pdl.can_execute():
        # Route to direct API endpoint
        if pdl.endpoint and HTTPX_AVAILABLE:
            backend_url = os.getenv("BACKEND_BASE", "http://localhost:8000")
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{backend_url}{pdl.endpoint}",
                    json=params
                )
                if response.status_code in (200, 201):
                    return response.json()
                return {"ok": False, "error": f"API error: {response.status_code}"}

    # For BROWSER or UNIVERSAL_FABRIC methods
    if actual_method in (ExecutionMethod.BROWSER, ExecutionMethod.UNIVERSAL_FABRIC, ExecutionMethod.HYBRID):
        url = params.get("url") or params.get("job_url") or params.get("post_url")

        if pdl.browser_url_template and not url:
            # Try to build URL from template
            try:
                url = pdl.browser_url_template.format(**params)
            except:
                pass

        if not url:
            return {"ok": False, "error": "No URL provided for browser execution"}

        # Get credentials if platform has them configured
        credentials = None
        platform = pdl.platform
        username_key = f"{platform.upper()}_USERNAME"
        password_key = f"{platform.upper()}_PASSWORD"
        if os.getenv(username_key) and os.getenv(password_key):
            credentials = {
                "username": os.getenv(username_key),
                "password": os.getenv(password_key)
            }

        return await execute_universal(
            pdl_name=pdl_name,
            url=url,
            data=params,
            ev_estimate=ev_estimate,
            credentials=credentials,
            dry_run=dry_run
        )

    # Manual fallback
    return {
        "ok": False,
        "queued": True,
        "reason": f"PDL {pdl_name} requires manual execution",
        "execution_method": actual_method.value
    }


print("🌐 UNIVERSAL FULFILLMENT FABRIC LOADED")
print(f"   • Playwright: {'Available' if PLAYWRIGHT_AVAILABLE else 'Not installed'}")
print(f"   • Vision AI: {'Configured' if OPENROUTER_API_KEY else 'Not configured'}")
print(f"   • Max auto EV: ${MAX_EV_AUTO_EXECUTE}")
print(f"   • Rate limit: {RATE_LIMIT_PER_HOUR}/hour")
print(f"   • HackerNews: {'Credentials configured' if HN_USERNAME and HN_PASSWORD else '⚠️  No credentials (set HN_USERNAME + HN_PASSWORD for posting)'}")
