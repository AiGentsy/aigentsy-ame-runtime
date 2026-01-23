"""
═══════════════════════════════════════════════════════════════════════════════
INTERNET-WIDE SEARCH SETUP
═══════════════════════════════════════════════════════════════════════════════

Provides unified internet search across multiple providers with automatic fallback:

1. Perplexity API (best for research, real-time data) - if PERPLEXITY_API_KEY set
2. Serper API (Google results) - if SERPER_API_KEY set
3. DuckDuckGo (FREE fallback) - always available

USAGE:
    from internet_search_setup import search_internet, include_search_endpoints

    # Search across all available providers
    results = await search_internet("AI automation tools 2024")

    # Wire endpoints into FastAPI
    include_search_endpoints(app)

ENDPOINTS:
    POST /search/internet       - Run internet-wide search
    GET  /search/providers      - List available search providers
    GET  /search/test           - Test all providers
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import aiohttp
import os
import json
import re

router = APIRouter(prefix="/search", tags=["Internet Search"])


def _now():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════════

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_available_providers() -> List[Dict[str, Any]]:
    """Get list of available search providers"""
    providers = []

    if PERPLEXITY_API_KEY:
        providers.append({
            "name": "perplexity",
            "priority": 1,
            "description": "Perplexity AI - Best for research and real-time data",
            "available": True,
            "rate_limit": "Varies by plan"
        })

    if SERPER_API_KEY:
        providers.append({
            "name": "serper",
            "priority": 2,
            "description": "Serper - Google search results API",
            "available": True,
            "rate_limit": "2500/month free tier"
        })

    # DuckDuckGo is always available (free, no API key)
    providers.append({
        "name": "duckduckgo",
        "priority": 3,
        "description": "DuckDuckGo Instant Answer API - Free fallback",
        "available": True,
        "rate_limit": "Unlimited (be reasonable)"
    })

    return providers


# ═══════════════════════════════════════════════════════════════════════════════
# PERPLEXITY SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

async def search_perplexity(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search using Perplexity API.

    Best for:
    - Real-time information
    - Research queries
    - Summarized answers with sources
    """
    if not PERPLEXITY_API_KEY:
        return {"ok": False, "error": "PERPLEXITY_API_KEY not set"}

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant. Provide concise, factual answers with sources. Focus on actionable information and opportunities."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.2,
                "return_citations": True,
                "return_images": False
            }

            async with session.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    citations = data.get("citations", [])

                    # Extract opportunities from response
                    opportunities = _extract_opportunities_from_text(content, "perplexity")

                    return {
                        "ok": True,
                        "provider": "perplexity",
                        "query": query,
                        "summary": content[:500],
                        "full_response": content,
                        "citations": citations[:max_results],
                        "opportunities": opportunities,
                        "timestamp": _now()
                    }
                else:
                    error_text = await resp.text()
                    return {"ok": False, "error": f"Perplexity API error: {resp.status} - {error_text}"}

    except Exception as e:
        return {"ok": False, "error": f"Perplexity search failed: {str(e)}"}


# ═══════════════════════════════════════════════════════════════════════════════
# SERPER SEARCH (Google Results)
# ═══════════════════════════════════════════════════════════════════════════════

async def search_serper(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search using Serper API (Google results).

    Best for:
    - Traditional web search
    - Finding specific pages/sites
    - News and recent content
    """
    if not SERPER_API_KEY:
        return {"ok": False, "error": "SERPER_API_KEY not set"}

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "q": query,
                "num": max_results
            }

            async with session.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload,
                timeout=15
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    results = []
                    for item in data.get("organic", [])[:max_results]:
                        results.append({
                            "title": item.get("title"),
                            "url": item.get("link"),
                            "snippet": item.get("snippet"),
                            "position": item.get("position")
                        })

                    # Extract opportunities
                    opportunities = []
                    for r in results:
                        opps = _extract_opportunities_from_text(
                            f"{r['title']} {r['snippet']}",
                            "serper",
                            url=r['url']
                        )
                        opportunities.extend(opps)

                    return {
                        "ok": True,
                        "provider": "serper",
                        "query": query,
                        "results": results,
                        "total_results": data.get("searchParameters", {}).get("num", 0),
                        "opportunities": opportunities[:10],
                        "timestamp": _now()
                    }
                else:
                    return {"ok": False, "error": f"Serper API error: {resp.status}"}

    except Exception as e:
        return {"ok": False, "error": f"Serper search failed: {str(e)}"}


# ═══════════════════════════════════════════════════════════════════════════════
# DUCKDUCKGO SEARCH (FREE FALLBACK)
# ═══════════════════════════════════════════════════════════════════════════════

async def search_duckduckgo(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search using DuckDuckGo Instant Answer API.

    Always available as FREE fallback.
    Uses the instant answer API + HTML scraping for more results.
    """
    try:
        async with aiohttp.ClientSession() as session:
            # DuckDuckGo Instant Answer API
            params = {
                "q": query,
                "format": "json",
                "no_redirect": 1,
                "no_html": 1,
                "skip_disambig": 1
            }

            results = []
            opportunities = []

            async with session.get(
                "https://api.duckduckgo.com/",
                params=params,
                timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    # Abstract (main answer)
                    if data.get("Abstract"):
                        results.append({
                            "title": data.get("Heading", "Summary"),
                            "url": data.get("AbstractURL", ""),
                            "snippet": data.get("Abstract"),
                            "source": data.get("AbstractSource", "")
                        })

                    # Related topics
                    for topic in data.get("RelatedTopics", [])[:max_results]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append({
                                "title": topic.get("Text", "")[:100],
                                "url": topic.get("FirstURL", ""),
                                "snippet": topic.get("Text", ""),
                                "source": "duckduckgo"
                            })

                    # Results (if any)
                    for r in data.get("Results", [])[:max_results]:
                        results.append({
                            "title": r.get("Text", "")[:100],
                            "url": r.get("FirstURL", ""),
                            "snippet": r.get("Text", ""),
                            "source": "duckduckgo"
                        })

            # Also try DuckDuckGo HTML search for more results
            html_results = await _scrape_duckduckgo_html(query, session, max_results)
            results.extend(html_results)

            # Dedupe by URL
            seen_urls = set()
            unique_results = []
            for r in results:
                if r.get("url") and r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    unique_results.append(r)

            # Extract opportunities
            for r in unique_results[:max_results]:
                opps = _extract_opportunities_from_text(
                    f"{r.get('title', '')} {r.get('snippet', '')}",
                    "duckduckgo",
                    url=r.get("url")
                )
                opportunities.extend(opps)

            return {
                "ok": True,
                "provider": "duckduckgo",
                "query": query,
                "results": unique_results[:max_results],
                "opportunities": opportunities[:10],
                "timestamp": _now()
            }

    except Exception as e:
        return {"ok": False, "error": f"DuckDuckGo search failed: {str(e)}"}


async def _scrape_duckduckgo_html(query: str, session: aiohttp.ClientSession, max_results: int) -> List[Dict]:
    """Scrape DuckDuckGo HTML results for additional data"""
    results = []

    try:
        # DuckDuckGo lite version (simpler HTML)
        params = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with session.get(
            "https://lite.duckduckgo.com/lite/",
            params=params,
            headers=headers,
            timeout=10
        ) as resp:
            if resp.status == 200:
                html = await resp.text()

                # Simple regex extraction (avoid BeautifulSoup dependency)
                # Look for result links
                link_pattern = r'<a[^>]*class="result-link"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                snippet_pattern = r'<td[^>]*class="result-snippet"[^>]*>([^<]*)</td>'

                links = re.findall(link_pattern, html)
                snippets = re.findall(snippet_pattern, html)

                for i, (url, title) in enumerate(links[:max_results]):
                    snippet = snippets[i] if i < len(snippets) else ""
                    if url and not url.startswith("/"):
                        results.append({
                            "title": title.strip(),
                            "url": url,
                            "snippet": snippet.strip(),
                            "source": "duckduckgo_html"
                        })

    except Exception as e:
        pass  # Silently fail HTML scraping

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# OPPORTUNITY EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_opportunities_from_text(text: str, source: str, url: str = None) -> List[Dict]:
    """Extract potential opportunities from search result text"""
    opportunities = []
    text_lower = text.lower()

    # Opportunity keywords
    opportunity_patterns = [
        # Job/Gig keywords
        (r"hiring|looking for|seeking|need|wanted", "job_opportunity", 500),
        (r"freelanc|contract|gig|project", "freelance_opportunity", 300),
        (r"remote|work from home|wfh", "remote_opportunity", 400),

        # Business keywords
        (r"startup|funding|invest|seed|series", "startup_opportunity", 1000),
        (r"partnership|collaboration|joint venture", "partnership_opportunity", 800),
        (r"grant|fellowship|scholarship", "funding_opportunity", 2000),

        # Sales keywords
        (r"rfp|rfq|tender|bid|proposal", "rfp_opportunity", 5000),
        (r"discount|sale|deal|offer", "deal_opportunity", 200),

        # Pain point keywords (potential service opportunity)
        (r"struggling|problem|issue|help|frustrated", "pain_point", 400),
        (r"recommend|suggestion|advice|best", "advice_request", 300),
    ]

    for pattern, opp_type, base_value in opportunity_patterns:
        if re.search(pattern, text_lower):
            opportunities.append({
                "id": f"search_opp_{uuid4().hex[:8]}",
                "type": opp_type,
                "source": source,
                "text_excerpt": text[:200],
                "url": url,
                "estimated_value": base_value,
                "confidence": 0.6,
                "detected_at": _now()
            })
            break  # One opportunity per result

    return opportunities


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED SEARCH FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

async def search_internet(
    query: str,
    max_results: int = 10,
    providers: List[str] = None
) -> Dict[str, Any]:
    """
    Search the internet using available providers with automatic fallback.

    Priority:
    1. Perplexity (if API key set) - best for research
    2. Serper (if API key set) - Google results
    3. DuckDuckGo (always available) - free fallback

    Args:
        query: Search query
        max_results: Max results per provider
        providers: Specific providers to use (None = auto)

    Returns:
        Combined results from all successful providers
    """
    search_id = f"search_{uuid4().hex[:8]}"
    results = {
        "search_id": search_id,
        "query": query,
        "timestamp": _now(),
        "providers_used": [],
        "all_results": [],
        "opportunities": [],
        "errors": []
    }

    # Determine which providers to use
    if providers:
        provider_list = providers
    else:
        provider_list = []
        if PERPLEXITY_API_KEY:
            provider_list.append("perplexity")
        if SERPER_API_KEY:
            provider_list.append("serper")
        provider_list.append("duckduckgo")  # Always include fallback

    # Run searches in parallel
    tasks = []
    for provider in provider_list:
        if provider == "perplexity":
            tasks.append(("perplexity", search_perplexity(query, max_results)))
        elif provider == "serper":
            tasks.append(("serper", search_serper(query, max_results)))
        elif provider == "duckduckgo":
            tasks.append(("duckduckgo", search_duckduckgo(query, max_results)))

    # Execute all searches
    for provider_name, task in tasks:
        try:
            result = await task
            if result.get("ok"):
                results["providers_used"].append(provider_name)

                # Add results
                if provider_name == "perplexity":
                    results["all_results"].append({
                        "provider": "perplexity",
                        "type": "summary",
                        "content": result.get("summary"),
                        "citations": result.get("citations", [])
                    })
                else:
                    for r in result.get("results", []):
                        results["all_results"].append({
                            "provider": provider_name,
                            "type": "link",
                            **r
                        })

                # Add opportunities
                results["opportunities"].extend(result.get("opportunities", []))
            else:
                results["errors"].append({
                    "provider": provider_name,
                    "error": result.get("error")
                })
        except Exception as e:
            results["errors"].append({
                "provider": provider_name,
                "error": str(e)
            })

    # Dedupe opportunities
    seen_urls = set()
    unique_opps = []
    for opp in results["opportunities"]:
        url = opp.get("url", opp.get("id"))
        if url not in seen_urls:
            seen_urls.add(url)
            unique_opps.append(opp)
    results["opportunities"] = unique_opps[:20]

    # Summary stats
    results["stats"] = {
        "providers_succeeded": len(results["providers_used"]),
        "total_results": len(results["all_results"]),
        "opportunities_found": len(results["opportunities"]),
        "total_estimated_value": sum(o.get("estimated_value", 0) for o in results["opportunities"])
    }

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/internet")
async def search_internet_endpoint(body: Dict = Body(...)):
    """
    Run internet-wide search across all available providers.

    Body:
        query: Search query (required)
        max_results: Max results per provider (default: 10)
        providers: Specific providers to use (optional)
    """
    query = body.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    return await search_internet(
        query=query,
        max_results=body.get("max_results", 10),
        providers=body.get("providers")
    )


@router.get("/providers")
async def list_providers():
    """List all available search providers and their status"""
    return {
        "ok": True,
        "providers": get_available_providers(),
        "timestamp": _now()
    }


@router.get("/test")
async def test_all_providers():
    """Test all search providers with a sample query"""
    test_query = "AI automation freelance opportunities 2024"

    results = {
        "test_query": test_query,
        "timestamp": _now(),
        "provider_tests": []
    }

    # Test Perplexity
    if PERPLEXITY_API_KEY:
        perp_result = await search_perplexity(test_query, 3)
        results["provider_tests"].append({
            "provider": "perplexity",
            "success": perp_result.get("ok", False),
            "results_count": len(perp_result.get("citations", [])) if perp_result.get("ok") else 0,
            "error": perp_result.get("error")
        })
    else:
        results["provider_tests"].append({
            "provider": "perplexity",
            "success": False,
            "error": "API key not configured"
        })

    # Test Serper
    if SERPER_API_KEY:
        serp_result = await search_serper(test_query, 3)
        results["provider_tests"].append({
            "provider": "serper",
            "success": serp_result.get("ok", False),
            "results_count": len(serp_result.get("results", [])) if serp_result.get("ok") else 0,
            "error": serp_result.get("error")
        })
    else:
        results["provider_tests"].append({
            "provider": "serper",
            "success": False,
            "error": "API key not configured"
        })

    # Test DuckDuckGo (always available)
    ddg_result = await search_duckduckgo(test_query, 3)
    results["provider_tests"].append({
        "provider": "duckduckgo",
        "success": ddg_result.get("ok", False),
        "results_count": len(ddg_result.get("results", [])) if ddg_result.get("ok") else 0,
        "error": ddg_result.get("error")
    })

    # Summary
    results["summary"] = {
        "total_providers": len(results["provider_tests"]),
        "working_providers": sum(1 for t in results["provider_tests"] if t["success"]),
        "total_test_results": sum(t.get("results_count", 0) for t in results["provider_tests"])
    }

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION WITH DISCOVERY ENGINES
# ═══════════════════════════════════════════════════════════════════════════════

async def internet_discovery_scan(
    keywords: List[str] = None,
    max_results_per_keyword: int = 5
) -> Dict[str, Any]:
    """
    Run internet-wide discovery scan for opportunities.

    Used by discovery engines to expand beyond known platforms.
    """
    keywords = keywords or [
        "freelance developer needed",
        "startup looking for",
        "hiring remote",
        "need help with automation",
        "AI consulting opportunity",
        "looking for contractor",
        "RFP software development",
        "need technical cofounder"
    ]

    all_opportunities = []
    all_results = []

    for keyword in keywords:
        result = await search_internet(keyword, max_results_per_keyword)
        all_opportunities.extend(result.get("opportunities", []))
        all_results.extend(result.get("all_results", []))

    # Dedupe and rank opportunities
    seen = set()
    unique_opps = []
    for opp in all_opportunities:
        key = opp.get("url") or opp.get("text_excerpt", "")[:50]
        if key not in seen:
            seen.add(key)
            unique_opps.append(opp)

    # Sort by value
    unique_opps.sort(key=lambda x: x.get("estimated_value", 0), reverse=True)

    return {
        "ok": True,
        "scan_id": f"internet_scan_{uuid4().hex[:8]}",
        "keywords_scanned": len(keywords),
        "total_results": len(all_results),
        "opportunities_found": len(unique_opps),
        "top_opportunities": unique_opps[:20],
        "total_estimated_value": sum(o.get("estimated_value", 0) for o in unique_opps),
        "timestamp": _now()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_search_endpoints(app):
    """Include internet search endpoints in FastAPI app"""
    app.include_router(router)

    providers = get_available_providers()
    provider_names = [p["name"] for p in providers]

    print("=" * 80)
    print("🌐 INTERNET-WIDE SEARCH LOADED")
    print("=" * 80)
    print(f"Available Providers: {', '.join(provider_names)}")
    print("Endpoints:")
    print("  POST /search/internet   - Run internet search")
    print("  GET  /search/providers  - List providers")
    print("  GET  /search/test       - Test all providers")
    print("=" * 80)
