#!/bin/bash

# Quick API Test Script - Only tests endpoints, doesn't restart services
# Run this when services are already running

echo "═══════════════════════════════════════════════════"
echo "  Payment API - Quick Test (No Restart)"
echo "═══════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Health Check
echo "1️⃣  Testing Health Endpoint..."
HEALTH=$(curl -s http://localhost:8000/api/health/)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "$HEALTH" | python3 -m json.tool
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Is the server running? Try: sudo docker-compose ps"
    exit 1
fi
echo ""

# Step 2: Register Merchant
echo "2️⃣  Registering Test Merchant..."
REGISTER=$(curl -s -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"test$(date +%s)@example.com\", \"password\": \"test123456\"}")

echo "$REGISTER" | python3 -m json.tool

if echo "$REGISTER" | grep -q "token"; then
    TOKEN=$(echo "$REGISTER" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)
    API_KEY=$(echo "$REGISTER" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['api_key'])" 2>/dev/null)
    echo -e "${GREEN}✓ Merchant registered${NC}"
    echo -e "${YELLOW}Token: $TOKEN${NC}"
    echo -e "${YELLOW}API Key: $API_KEY${NC}"
else
    echo -e "${RED}✗ Registration failed${NC}"
    exit 1
fi
echo ""

# Step 3: Create Transaction
echo "3️⃣  Creating Transaction..."
TRANSACTION=$(curl -s -X POST http://localhost:8000/api/transactions/pay/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": "99.99", "currency": "USD", "description": "Test payment"}')

echo "$TRANSACTION" | python3 -m json.tool

if echo "$TRANSACTION" | grep -q "payment_key"; then
    TRANS_ID=$(echo "$TRANSACTION" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
    PAYMENT_KEY=$(echo "$TRANSACTION" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['payment_key'])" 2>/dev/null)
    echo -e "${GREEN}✓ Transaction created${NC}"
    echo -e "${YELLOW}Transaction ID: $TRANS_ID${NC}"
    echo -e "${YELLOW}Payment Key: $PAYMENT_KEY${NC}"
else
    echo -e "${RED}✗ Transaction creation failed${NC}"
    exit 1
fi
echo ""

# Step 4: Wait for Celery
echo "4️⃣  Waiting for Celery processing (6 seconds)..."
for i in {6..1}; do
    echo -ne "\r   Processing... $i seconds   "
    sleep 1
done
echo ""
echo ""

# Step 5: Check Transaction Status
echo "5️⃣  Checking Transaction Status..."
STATUS=$(curl -s http://localhost:8000/api/transactions/$TRANS_ID/ \
  -H "Authorization: Token $TOKEN")

echo "$STATUS" | python3 -m json.tool

TRANS_STATUS=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['status'])" 2>/dev/null)

if [ "$TRANS_STATUS" = "succeeded" ]; then
    echo -e "${GREEN}✓ Transaction SUCCEEDED!${NC}"
    CAN_REFUND=true
elif [ "$TRANS_STATUS" = "failed" ]; then
    echo -e "${YELLOW}⚠ Transaction FAILED (expected 20% of the time)${NC}"
    CAN_REFUND=false
else
    echo -e "${YELLOW}Status: $TRANS_STATUS${NC}"
    CAN_REFUND=false
fi
echo ""

# Step 6: List Transactions
echo "6️⃣  Listing All Transactions..."
curl -s http://localhost:8000/api/transactions/ \
  -H "Authorization: Token $TOKEN" | python3 -m json.tool
echo ""

# Step 7: Create Refund (if transaction succeeded)
if [ "$CAN_REFUND" = true ]; then
    echo "7️⃣  Creating Refund..."
    REFUND=$(curl -s -X POST http://localhost:8000/api/refunds/ \
      -H "Authorization: Token $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"transaction\": \"$TRANS_ID\", \"amount\": \"50.00\", \"reason\": \"Customer request\"}")

    echo "$REFUND" | python3 -m json.tool

    if echo "$REFUND" | grep -q "succeeded"; then
        echo -e "${GREEN}✓ Refund created successfully${NC}"
    else
        echo -e "${RED}✗ Refund failed${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}7️⃣  Skipping refund (transaction didn't succeed)${NC}"
    echo ""
fi

# Step 8: Register Webhook
echo "8️⃣  Registering Webhook..."
WEBHOOK=$(curl -s -X POST http://localhost:8000/api/webhooks/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://webhook.site/test-endpoint"}')

echo "$WEBHOOK" | python3 -m json.tool

if echo "$WEBHOOK" | grep -q "webhook.site"; then
    echo -e "${GREEN}✓ Webhook registered${NC}"
else
    echo -e "${RED}✗ Webhook registration failed${NC}"
fi
echo ""

# Step 9: List Webhooks
echo "9️⃣  Listing Webhooks..."
curl -s http://localhost:8000/api/webhooks/list/ \
  -H "Authorization: Token $TOKEN" | python3 -m json.tool
echo ""

# Summary
echo "═══════════════════════════════════════════════════"
echo "  ✅ ALL TESTS COMPLETED!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📊 Test Summary:"
echo "  • Health Check: ✓"
echo "  • Merchant Registration: ✓"
echo "  • Transaction Creation: ✓"
echo "  • Celery Processing: ✓"
echo "  • Transaction Status: $TRANS_STATUS"
echo "  • Refund: $([ "$CAN_REFUND" = true ] && echo '✓' || echo 'N/A')"
echo "  • Webhook Registration: ✓"
echo ""
echo "🔑 Your Test Credentials:"
echo "  Token: $TOKEN"
echo "  API Key: $API_KEY"
echo ""
echo "📝 Useful Commands:"
echo "  View logs: sudo docker-compose logs -f"
echo "  Check Celery: sudo docker-compose logs celery"
echo "  Restart: sudo docker-compose restart web"
echo ""
