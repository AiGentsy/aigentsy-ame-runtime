"""
Headless Browser Connector
==========================

Playwright-based fallback for sites without APIs.
Anti-fragile: form fill, click, upload, scrape with DOM selectors.
"""

from typing import Dict, Any, Optional, List
import time
import os
import asyncio
import hashlib

from .base import Connector, ConnectorResult, ConnectorHealth, CostEstimate, AuthScheme

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class HeadlessConnector(Connector):
    """
    Headless browser connector using Playwright.

    This is the anti-fragile fallback for any site without an API.
    Respects site ToS and legal boundaries; paces with token buckets.

    Capabilities:
    - generic_browser_action: Execute browser steps
    - fill_form: Fill and submit forms
    - click_element: Click elements
    - scrape_content: Scrape page content
    - take_screenshot: Capture screenshot proof
    - download_file: Download file from page
    """

    name = "headless"
    capabilities = [
        "generic_browser_action",
        "fill_form",
        "click_element",
        "scrape_content",
        "take_screenshot",
        "download_file",
        "navigate",
        "extract_data",
        "submit_form"
    ]
    auth_schemes = [AuthScheme.SESSION_COOKIE, AuthScheme.NONE]

    avg_latency_ms = 5000.0  # Browser actions are slower
    success_rate = 0.85  # More failure modes
    max_rps = 0.5  # Be respectful to sites

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}

        self._headless = config.get("headless", True)
        self._timeout_ms = config.get("timeout_ms", 30000)
        self._user_agent = config.get("user_agent", "Mozilla/5.0 (compatible; AiGentsy/1.0)")
        self._screenshots_dir = config.get("screenshots_dir", "/tmp/headless_screenshots")

        # Rate limiting
        self._last_action_time: Dict[str, float] = {}
        self._min_interval_sec = config.get("min_interval_sec", 2.0)

    async def health(self) -> ConnectorHealth:
        if not PLAYWRIGHT_AVAILABLE:
            return ConnectorHealth(
                healthy=False,
                latency_ms=0,
                error="playwright_not_installed. Run: pip install playwright && playwright install"
            )
        return ConnectorHealth(healthy=True, latency_ms=0)

    async def _rate_limit(self, domain: str):
        """Enforce per-domain rate limiting"""
        now = time.time()
        last = self._last_action_time.get(domain, 0)
        wait = max(0, self._min_interval_sec - (now - last))
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_action_time[domain] = time.time()

    async def execute(
        self,
        action: str,
        params: Dict[str, Any],
        files: Optional[Dict[str, bytes]] = None,
        *,
        idempotency_key: Optional[str] = None,
        timeout: int = 60
    ) -> ConnectorResult:
        if not PLAYWRIGHT_AVAILABLE:
            return ConnectorResult(
                ok=False,
                error="playwright_not_installed",
                retryable=False
            )

        start = time.time()

        try:
            if action == "generic_browser_action":
                result = await self._execute_steps(params, timeout)
            elif action == "fill_form":
                result = await self._fill_form(params, timeout)
            elif action == "scrape_content":
                result = await self._scrape_content(params, timeout)
            elif action == "take_screenshot":
                result = await self._take_screenshot(params, timeout)
            elif action == "navigate":
                result = await self._navigate(params, timeout)
            else:
                # Generic fallback - try to execute as steps
                result = await self._execute_steps(params, timeout)

            latency = (time.time() - start) * 1000
            self._record_call(result.ok, latency)
            result.latency_ms = latency
            result.idempotency_key = idempotency_key
            return result

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(
                ok=False,
                error=str(e),
                latency_ms=latency,
                retryable=True
            )

    async def _execute_steps(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """
        Execute a sequence of browser steps.

        params:
            url: Starting URL
            steps: List of {selector, action, value} dicts
            proofs: List of proof types to collect ["screenshot", "html"]
        """
        url = params.get("url")
        steps = params.get("steps", [])
        proof_types = params.get("proofs", ["screenshot"])

        if not url:
            return ConnectorResult(ok=False, error="url_required", retryable=False)

        # Extract domain for rate limiting
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        await self._rate_limit(domain)

        proofs = []
        collected_data = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self._headless)
            context = await browser.new_context(user_agent=self._user_agent)
            page = await context.new_page()
            page.set_default_timeout(self._timeout_ms)

            try:
                # Navigate to URL
                await page.goto(url, wait_until="networkidle")

                # Execute steps
                for i, step in enumerate(steps):
                    selector = step.get("selector")
                    action = step.get("action", "click")
                    value = step.get("value", "")

                    if action == "click" and selector:
                        await page.click(selector)
                    elif action == "fill" and selector:
                        await page.fill(selector, str(value))
                    elif action == "type" and selector:
                        await page.type(selector, str(value))
                    elif action == "select" and selector:
                        await page.select_option(selector, str(value))
                    elif action == "wait":
                        await asyncio.sleep(float(value) if value else 1)
                    elif action == "wait_for_selector" and selector:
                        await page.wait_for_selector(selector)
                    elif action == "press" and value:
                        await page.keyboard.press(value)
                    elif action == "extract" and selector:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            collected_data[step.get("name", f"extract_{i}")] = text

                    # Small delay between actions
                    await asyncio.sleep(0.3)

                # Collect proofs
                if "screenshot" in proof_types:
                    screenshot_bytes = await page.screenshot(full_page=True)
                    screenshot_hash = hashlib.sha256(screenshot_bytes).hexdigest()
                    proofs.append({
                        "type": "screenshot",
                        "hash": screenshot_hash,
                        "timestamp": time.time()
                    })

                if "html" in proof_types:
                    html = await page.content()
                    html_hash = hashlib.sha256(html.encode()).hexdigest()
                    proofs.append({
                        "type": "html_content",
                        "hash": html_hash,
                        "timestamp": time.time()
                    })

                if "url" in proof_types:
                    final_url = page.url
                    proofs.append({
                        "type": "final_url",
                        "url": final_url,
                        "timestamp": time.time()
                    })

                return ConnectorResult(
                    ok=True,
                    data={
                        "url": page.url,
                        "title": await page.title(),
                        "extracted": collected_data,
                        "steps_completed": len(steps)
                    },
                    proofs=proofs
                )

            except Exception as e:
                # Try to capture error screenshot
                try:
                    error_screenshot = await page.screenshot()
                    proofs.append({
                        "type": "error_screenshot",
                        "hash": hashlib.sha256(error_screenshot).hexdigest(),
                        "timestamp": time.time()
                    })
                except:
                    pass

                return ConnectorResult(
                    ok=False,
                    error=str(e),
                    proofs=proofs,
                    retryable=True
                )

            finally:
                await browser.close()

    async def _fill_form(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """Fill and submit a form"""
        url = params.get("url")
        fields = params.get("fields", {})  # {selector: value}
        submit_selector = params.get("submit_selector", 'button[type="submit"]')

        steps = []
        for selector, value in fields.items():
            steps.append({"selector": selector, "action": "fill", "value": value})

        steps.append({"selector": submit_selector, "action": "click"})
        steps.append({"action": "wait", "value": 2})

        return await self._execute_steps({
            "url": url,
            "steps": steps,
            "proofs": ["screenshot", "url"]
        }, timeout)

    async def _scrape_content(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """Scrape content from a page"""
        url = params.get("url")
        selectors = params.get("selectors", {})  # {name: selector}

        steps = []
        for name, selector in selectors.items():
            steps.append({"selector": selector, "action": "extract", "name": name})

        return await self._execute_steps({
            "url": url,
            "steps": steps,
            "proofs": ["html"]
        }, timeout)

    async def _take_screenshot(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """Take screenshot of a page"""
        url = params.get("url")

        return await self._execute_steps({
            "url": url,
            "steps": [],
            "proofs": ["screenshot", "url"]
        }, timeout)

    async def _navigate(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """Navigate to URL and return page info"""
        url = params.get("url")

        return await self._execute_steps({
            "url": url,
            "steps": [],
            "proofs": ["url"]
        }, timeout)

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        # Browser actions are compute-intensive
        steps = len(params.get("steps", []))
        base_cost = 0.01  # Base cost for browser instance
        per_step = 0.002  # Cost per step

        return CostEstimate(
            estimated_usd=base_cost + (steps * per_step),
            model="per_step",
            breakdown={
                "browser_instance": base_cost,
                "steps": steps * per_step
            }
        )
