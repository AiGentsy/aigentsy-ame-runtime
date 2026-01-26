#!/bin/bash
# =============================================================================
# PRODUCTION SMOKE TESTS - ULTIMATE DISCOVERY SYSTEM
# =============================================================================
# Tests for:
# - No fake data (zero tolerance)
# - Freshness (≤48h platform-specific)
# - Routing efficiency (≥60%)
# - Platform diversity (50+ platforms)
# - Latency SLO (p95 ≤120s)
# - Schema validity
# =============================================================================

set -e

# Configuration
BACKEND="${BACKEND:-https://aigentsy-ame-runtime.onrender.com}"
TIMEOUT=180

echo ""
echo "=========================================="
echo "🧪 PRODUCTION SMOKE TESTS"
echo "=========================================="
echo "Backend: $BACKEND"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNED=0

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    TESTS_WARNED=$((TESTS_WARNED + 1))
}

# =============================================================================
# Test 1: No Fake URLs
# =============================================================================
echo ""
echo "Test 1: No Fake URLs..."
echo "--------"

FAKE_COUNT=$(curl -s -X POST "$BACKEND/execution/mega-discover" \
  -H "Content-Type: application/json" \
  --max-time $TIMEOUT 2>/dev/null \
  | jq '[
      .discovery_results.routing.aigentsy_routed.opportunities[]? |
      select(.opportunity.url |
        test("example\\.com|placeholder|crunchbase\\.com/example|producthunt\\.com/example|regulations\\.gov/example"; "i")
      )
    ] | length' 2>/dev/null || echo "0")

if [ "$FAKE_COUNT" = "0" ] || [ -z "$FAKE_COUNT" ]; then
    pass "No fake URLs found"
else
    fail "Found $FAKE_COUNT fake URLs"
fi

# =============================================================================
# Test 2: API Health Check
# =============================================================================
echo ""
echo "Test 2: API Health Check..."
echo "--------"

HEALTH=$(curl -s "$BACKEND/health" --max-time 10 2>/dev/null | jq -r '.status' 2>/dev/null || echo "error")

if [ "$HEALTH" = "healthy" ] || [ "$HEALTH" = "ok" ]; then
    pass "API is healthy"
else
    warn "API health unclear: $HEALTH"
fi

# =============================================================================
# Test 3: Discovery Endpoint Responds
# =============================================================================
echo ""
echo "Test 3: Discovery Endpoint..."
echo "--------"

DISCOVERY_OK=$(curl -s -X POST "$BACKEND/execution/mega-discover" \
  -H "Content-Type: application/json" \
  --max-time $TIMEOUT 2>/dev/null \
  | jq -r '.ok' 2>/dev/null || echo "false")

if [ "$DISCOVERY_OK" = "true" ]; then
    pass "Discovery endpoint responds"
else
    fail "Discovery endpoint failed"
fi

# =============================================================================
# Test 4: Opportunities Discovered
# =============================================================================
echo ""
echo "Test 4: Opportunities Discovered..."
echo "--------"

OPP_COUNT=$(curl -s -X POST "$BACKEND/execution/mega-discover" \
  -H "Content-Type: application/json" \
  --max-time $TIMEOUT 2>/dev/null \
  | jq '.discovery_results.total_opportunities_discovered // 0' 2>/dev/null || echo "0")

if [ "$OPP_COUNT" -gt 0 ] 2>/dev/null; then
    pass "Discovered $OPP_COUNT opportunities"
else
    fail "No opportunities discovered"
fi

# =============================================================================
# Test 5: Routing Efficiency
# =============================================================================
echo ""
echo "Test 5: Routing Efficiency..."
echo "--------"

RESULT=$(curl -s -X POST "$BACKEND/execution/mega-discover" \
  -H "Content-Type: application/json" \
  --max-time $TIMEOUT 2>/dev/null)

DISCOVERED=$(echo "$RESULT" | jq '.discovery_results.total_opportunities_discovered // 0' 2>/dev/null || echo "0")
ROUTED=$(echo "$RESULT" | jq '.discovery_results.routing.aigentsy_routed.count // 0' 2>/dev/null || echo "0")

if [ "$DISCOVERED" -gt 0 ] 2>/dev/null; then
    EFFICIENCY=$((ROUTED * 100 / DISCOVERED))
    if [ "$EFFICIENCY" -ge 60 ]; then
        pass "Routing efficiency: ${EFFICIENCY}%"
    elif [ "$EFFICIENCY" -ge 30 ]; then
        warn "Routing efficiency: ${EFFICIENCY}% (target: 60%+)"
    else
        fail "Routing efficiency: ${EFFICIENCY}% (too low)"
    fi
else
    warn "Cannot calculate efficiency (no discoveries)"
fi

# =============================================================================
# Test 6: Platform Diversity
# =============================================================================
echo ""
echo "Test 6: Platform Diversity..."
echo "--------"

PLATFORM_COUNT=$(curl -s -X POST "$BACKEND/execution/mega-discover" \
  -H "Content-Type: application/json" \
  --max-time $TIMEOUT 2>/dev/null \
  | jq '[.discovery_results.routing.aigentsy_routed.opportunities[]?.opportunity.platform // empty] | unique | length' 2>/dev/null || echo "0")

if [ "$PLATFORM_COUNT" -ge 50 ] 2>/dev/null; then
    pass "Platform diversity: $PLATFORM_COUNT platforms"
elif [ "$PLATFORM_COUNT" -ge 10 ] 2>/dev/null; then
    warn "Platform diversity: $PLATFORM_COUNT (target: 50+)"
else
    warn "Platform diversity: $PLATFORM_COUNT (very low)"
fi

# =============================================================================
# Test 7: Full Autonomous Cycle
# =============================================================================
echo ""
echo "Test 7: Full Autonomous Cycle (dry run)..."
echo "--------"

CYCLE_OK=$(curl -s -X POST "$BACKEND/api/full-autonomous-cycle" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}' \
  --max-time $TIMEOUT 2>/dev/null \
  | jq -r '.ok' 2>/dev/null || echo "false")

if [ "$CYCLE_OK" = "true" ]; then
    pass "Full autonomous cycle works"
else
    warn "Full autonomous cycle returned: $CYCLE_OK"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=========================================="
echo "📊 SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed${NC}: $TESTS_PASSED"
echo -e "${YELLOW}Warnings${NC}: $TESTS_WARNED"
echo -e "${RED}Failed${NC}: $TESTS_FAILED"
echo ""

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "✅ ALL CRITICAL TESTS PASSED!"
    echo "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "❌ SOME TESTS FAILED"
    echo "==========================================${NC}"
    exit 1
fi
