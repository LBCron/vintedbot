#!/bin/bash
set -e

echo "🔍 VALIDATING DEPLOYMENT"
echo "======================="

API_URL="${1:-https://vintedbot-staging.fly.dev}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

passed=0
failed=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="$3"
    
    echo -n "Testing $name... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$status" == "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status)"
        ((passed++))
    else
        echo -e "${RED}❌ FAIL${NC} (Expected $expected_status, got $status)"
        ((failed++))
    fi
}

echo ""
echo "Testing endpoints..."
echo ""

# Health check
test_endpoint "Health Check" "${API_URL}/health" "200"

# API docs
test_endpoint "API Docs" "${API_URL}/docs" "200"

# Plans endpoint (public)
test_endpoint "Payment Plans" "${API_URL}/api/v1/payments/plans" "200"

# Webhook events (public)
test_endpoint "Webhook Events" "${API_URL}/api/v1/webhooks/events" "200"

# Protected endpoint (should return 401)
test_endpoint "Protected Endpoint" "${API_URL}/api/v1/listings" "401"

# Admin endpoint (should return 401/403)
echo -n "Testing Admin Endpoint... "
status=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/v1/admin/stats" || echo "000")
if [ "$status" == "401" ] || [ "$status" == "403" ]; then
    echo -e "${GREEN}✅ PASS${NC} (HTTP $status - properly protected)"
    ((passed++))
else
    echo -e "${RED}❌ FAIL${NC} (Expected 401/403, got $status)"
    ((failed++))
fi

echo ""
echo "Results:"
echo -e "✅ Passed: $passed"
echo -e "❌ Failed: $failed"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
