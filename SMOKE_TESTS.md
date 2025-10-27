# Smoke Tests (curl)

# Oracle PAID -> R3 enqueue
curl -X POST $BACKEND_BASE/oracle/event -H 'Content-Type: application/json' -d '{
  "user_id":"admin4","source":"shopify","kind":"PAID","amount_usd":49.0
}'

# R3 allocate
curl -X POST $BACKEND_BASE/r3/allocate -H 'Content-Type: application/json' -d '{
  "user_id":"admin4","budget_usd":25
}'

# Intent publish/claim/settle
curl -X POST $BACKEND_BASE/intents/publish -H 'Content-Type: application/json' -d '{
  "user_id":"admin4","intent":{"title":"Need landing page","bounty_usd":150}
}'
