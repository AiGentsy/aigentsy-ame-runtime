
#!/usr/bin/env bash
set -euo pipefail
export FLASK_DEBUG=0
if [ -f .env ]; then
  set -a; source .env; set +a
fi
python3 -m pip install -r requirements_webhook.txt
python3 shopify_webhook.py
