
# Shopify Webhook for AiGentsy AAM

## What this does
- Verifies Shopify HMAC (`X-Shopify-Hmac-Sha256`)
- Reads topic (`X-Shopify-Topic`)
- `orders/create` → Outcome Oracle **ATTRIBUTED**
- `orders/paid` or `orders/fulfilled` → **PAID** (+ credits AIGx in JSONBin)

## Configure
Add to your `.env`:
```
SHOPIFY_WEBHOOK_SECRET=***
SHOPIFY_SHOP_TO_USER={"my-shop.myshopify.com":"wade888"}
DEFAULT_USERNAME=demo_user
COMMISSION_RATE=0.05
JSONBIN_URL=***
JSONBIN_SECRET=***
BACKEND_BASE=***
```
(You already have the JSONBin/Backend variables from earlier steps.)

## Run locally
```
./run_webhook_locally.sh
```
or
```
python3 -m pip install -r requirements_webhook.txt
flask --app shopify_webhook:app run -h 0.0.0.0 -p 8080
```

## Test
When testing without Shopify, compute a valid HMAC:
```
BODY=$(cat sample_shopify_order_create.json)
HMAC=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SHOPIFY_WEBHOOK_SECRET" -binary | base64)
curl -s -X POST http://localhost:8080/webhooks/shopify   -H "Content-Type: application/json"   -H "X-Shopify-Topic: orders/create"   -H "X-Shopify-Shop-Domain: my-shop.myshopify.com"   -H "X-Shopify-Hmac-Sha256: $HMAC"   -d "$BODY"
```

## Deploy
```
pip install -r requirements_webhook.txt
gunicorn -w 2 -b 0.0.0.0:8080 shopify_webhook:app
```
Then in Shopify Admin → Webhooks, point to:
- `https://YOUR_DOMAIN/webhooks/shopify` for topics `orders/create`, `orders/paid`, (optional) `orders/fulfilled`.
