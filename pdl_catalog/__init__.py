"""
Protocol Descriptor Language (PDL) Catalog
==========================================

PDL defines how to perform outcomes on any system using a declarative YAML/JSON spec.

Each PDL declares:
- name: Unique outcome identifier
- connector: Which connector to use
- action: The connector action
- inputs: Required/optional input parameters
- sla: Performance expectations
- proofs: What evidence to collect
- cost_model: How to estimate costs

Usage:
    from pdl_catalog import PDLCatalog, load_pdl

    catalog = PDLCatalog()
    catalog.load_builtin()

    pdl = catalog.get("shopify.create_product")
    outcome = pdl.to_outcome({"title": "My Product", "price": 29.99})
"""

import os
import json
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class PDLSpec:
    """
    Protocol Descriptor Language specification.

    Defines how to perform an outcome on a given system.
    """

    def __init__(self, spec: Dict[str, Any]):
        self.name = spec.get("name", "")
        self.connector = spec.get("connector", "")
        self.action = spec.get("action", "")
        self.description = spec.get("description", "")

        self.inputs = spec.get("inputs", [])
        self.sla = spec.get("sla", {"p50_ms": 5000, "p99_ms": 30000})
        self.proofs = spec.get("proofs", [])
        self.cost_model = spec.get("cost_model", {"type": "per_call", "unit_cost_usd": 0.01})

        # Optional fields
        self.fallback_connector = spec.get("fallback_connector")
        self.retry_policy = spec.get("retry_policy", {"max_retries": 3, "backoff_ms": 1000})
        self.validation = spec.get("validation", {})
        self.tags = spec.get("tags", [])

        self._raw = spec

    def validate_inputs(self, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate input parameters against spec"""
        errors = []

        for input_spec in self.inputs:
            key = input_spec.get("key")
            required = input_spec.get("required", False)
            input_type = input_spec.get("type", "string")

            if required and key not in params:
                errors.append(f"missing_required_input:{key}")
                continue

            if key in params:
                value = params[key]
                # Type checking
                if input_type == "string" and not isinstance(value, str):
                    errors.append(f"invalid_type:{key}:expected_string")
                elif input_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"invalid_type:{key}:expected_number")
                elif input_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"invalid_type:{key}:expected_boolean")
                elif input_type == "array" and not isinstance(value, list):
                    errors.append(f"invalid_type:{key}:expected_array")
                elif input_type == "object" and not isinstance(value, dict):
                    errors.append(f"invalid_type:{key}:expected_object")

        return len(errors) == 0, errors

    def to_outcome(
        self,
        params: Dict[str, Any],
        *,
        idempotency_key: Optional[str] = None,
        pricing_override: Optional[Dict[str, Any]] = None,
        risk_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert PDL + params to a Contractable Outcome Interface (COI) spec.
        """
        # Validate inputs
        valid, errors = self.validate_inputs(params)
        if not valid:
            raise ValueError(f"Invalid inputs: {errors}")

        # Build outcome spec
        outcome = {
            "outcome_type": self.action,
            "inputs": params,
            "sla": {
                "deadline_sec": self.sla.get("p99_ms", 30000) / 1000,
                "success_criteria": self.proofs
            },
            "pricing": pricing_override or {
                "model": self.cost_model.get("type", "fixed"),
                "amount_usd": self.cost_model.get("unit_cost_usd", 0.01)
            },
            "risk": risk_override or {
                "bond_usd": self.cost_model.get("unit_cost_usd", 0.01) * 10,
                "insurance_pct": 3.5
            },
            "proofs": self.proofs,
            "idempotency_key": idempotency_key or "",

            # Metadata
            "_pdl": self.name,
            "_connector": self.connector,
            "_fallback": self.fallback_connector
        }

        return outcome

    def estimate_cost(self, params: Dict[str, Any]) -> float:
        """Estimate cost for executing this outcome"""
        cost_type = self.cost_model.get("type", "per_call")
        unit_cost = self.cost_model.get("unit_cost_usd", 0.01)

        if cost_type == "per_call":
            return unit_cost
        elif cost_type == "per_unit":
            units = params.get("units", 1)
            return unit_cost * units
        elif cost_type == "percentage":
            amount = params.get("amount", 0)
            return amount * unit_cost
        else:
            return unit_cost

    def to_dict(self) -> Dict[str, Any]:
        return self._raw


class PDLCatalog:
    """
    Central catalog of all Protocol Descriptors.
    """

    def __init__(self):
        self._pdls: Dict[str, PDLSpec] = {}
        self._tags_index: Dict[str, List[str]] = {}

    def register(self, pdl: PDLSpec) -> None:
        """Register a PDL in the catalog"""
        self._pdls[pdl.name] = pdl

        # Index by tags
        for tag in pdl.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = []
            self._tags_index[tag].append(pdl.name)

    def get(self, name: str) -> Optional[PDLSpec]:
        """Get a PDL by name"""
        return self._pdls.get(name)

    def find_by_tag(self, tag: str) -> List[PDLSpec]:
        """Find PDLs by tag"""
        names = self._tags_index.get(tag, [])
        return [self._pdls[n] for n in names if n in self._pdls]

    def find_by_connector(self, connector: str) -> List[PDLSpec]:
        """Find all PDLs using a connector"""
        return [pdl for pdl in self._pdls.values() if pdl.connector == connector]

    def all(self) -> List[PDLSpec]:
        """Get all PDLs"""
        return list(self._pdls.values())

    def load_from_file(self, path: str) -> None:
        """Load PDL from YAML or JSON file"""
        with open(path) as f:
            if path.endswith(".yaml") or path.endswith(".yml"):
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)

        if isinstance(spec, list):
            for s in spec:
                self.register(PDLSpec(s))
        else:
            self.register(PDLSpec(spec))

    def load_from_dir(self, directory: str) -> None:
        """Load all PDLs from directory"""
        path = Path(directory)
        for file in path.glob("**/*.yaml"):
            self.load_from_file(str(file))
        for file in path.glob("**/*.yml"):
            self.load_from_file(str(file))
        for file in path.glob("**/*.json"):
            self.load_from_file(str(file))

    def load_builtin(self) -> None:
        """Load built-in PDL catalog"""
        builtin_pdls = get_builtin_pdls()
        for spec in builtin_pdls:
            self.register(PDLSpec(spec))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pdls": {name: pdl.to_dict() for name, pdl in self._pdls.items()},
            "count": len(self._pdls)
        }


def get_builtin_pdls() -> List[Dict[str, Any]]:
    """Return built-in PDL specifications"""
    return [
        # ====== EMAIL ======
        {
            "name": "email.send",
            "connector": "email",
            "action": "send_email",
            "description": "Send an email via Postmark/SendGrid",
            "inputs": [
                {"key": "to", "type": "string", "required": True},
                {"key": "subject", "type": "string", "required": True},
                {"key": "body", "type": "string", "required": True},
                {"key": "html", "type": "string", "required": False}
            ],
            "sla": {"p50_ms": 800, "p99_ms": 3000},
            "proofs": ["message_id", "delivery_status"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.001},
            "tags": ["communication", "email"]
        },
        {
            "name": "email.nudge",
            "connector": "email",
            "action": "send_email_nudge",
            "description": "Send cart abandonment or follow-up nudge email",
            "inputs": [
                {"key": "to", "type": "string", "required": True},
                {"key": "subject", "type": "string", "required": False},
                {"key": "body", "type": "string", "required": False},
                {"key": "template", "type": "string", "required": False}
            ],
            "sla": {"p50_ms": 1000, "p99_ms": 5000},
            "proofs": ["message_id"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.001},
            "tags": ["communication", "email", "nudge", "cart_recovery"]
        },

        # ====== SMS ======
        {
            "name": "sms.send",
            "connector": "sms",
            "action": "send_sms",
            "description": "Send SMS via Twilio",
            "inputs": [
                {"key": "to", "type": "string", "required": True},
                {"key": "body", "type": "string", "required": True}
            ],
            "sla": {"p50_ms": 1200, "p99_ms": 5000},
            "proofs": ["message_sid", "delivery_status"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.008},
            "tags": ["communication", "sms"]
        },

        # ====== SLACK ======
        {
            "name": "slack.message",
            "connector": "slack",
            "action": "send_slack_message",
            "description": "Send message to Slack channel or DM",
            "inputs": [
                {"key": "channel", "type": "string", "required": False},
                {"key": "text", "type": "string", "required": True},
                {"key": "blocks", "type": "array", "required": False}
            ],
            "sla": {"p50_ms": 400, "p99_ms": 2000},
            "proofs": ["message_ts", "channel"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.0001},
            "tags": ["communication", "slack"]
        },

        # ====== SHOPIFY ======
        {
            "name": "shopify.create_product",
            "connector": "shopify",
            "action": "create_product",
            "description": "Create a new product in Shopify store",
            "inputs": [
                {"key": "title", "type": "string", "required": True},
                {"key": "price", "type": "number", "required": True},
                {"key": "description", "type": "string", "required": False},
                {"key": "images", "type": "array", "required": False},
                {"key": "sku", "type": "string", "required": False},
                {"key": "inventory", "type": "number", "required": False}
            ],
            "sla": {"p50_ms": 1200, "p99_ms": 5000},
            "proofs": ["api_response", "product_url", "product_id"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.002},
            "tags": ["ecommerce", "shopify", "product"]
        },
        {
            "name": "shopify.create_order",
            "connector": "shopify",
            "action": "create_order",
            "description": "Create a draft order in Shopify",
            "inputs": [
                {"key": "line_items", "type": "array", "required": True},
                {"key": "customer", "type": "object", "required": False}
            ],
            "sla": {"p50_ms": 1500, "p99_ms": 6000},
            "proofs": ["order_id", "invoice_url"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.002},
            "tags": ["ecommerce", "shopify", "order"]
        },
        {
            "name": "shopify.create_discount",
            "connector": "shopify",
            "action": "create_discount_code",
            "description": "Create a discount code in Shopify",
            "inputs": [
                {"key": "title", "type": "string", "required": False},
                {"key": "amount_pct", "type": "number", "required": True}
            ],
            "sla": {"p50_ms": 1000, "p99_ms": 4000},
            "proofs": ["price_rule_id"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.002},
            "tags": ["ecommerce", "shopify", "discount"]
        },

        # ====== STRIPE ======
        {
            "name": "stripe.payment_link",
            "connector": "stripe",
            "action": "create_payment_link",
            "description": "Create a Stripe payment link",
            "inputs": [
                {"key": "amount", "type": "number", "required": True},
                {"key": "currency", "type": "string", "required": False},
                {"key": "description", "type": "string", "required": False},
                {"key": "metadata", "type": "object", "required": False}
            ],
            "sla": {"p50_ms": 800, "p99_ms": 3000},
            "proofs": ["payment_link_id", "payment_link_url"],
            "cost_model": {"type": "percentage", "unit_cost_usd": 0.029},
            "tags": ["payment", "stripe"]
        },
        {
            "name": "stripe.invoice",
            "connector": "stripe",
            "action": "create_invoice",
            "description": "Create and send a Stripe invoice",
            "inputs": [
                {"key": "customer_id", "type": "string", "required": True},
                {"key": "amount", "type": "number", "required": True},
                {"key": "description", "type": "string", "required": False},
                {"key": "days_due", "type": "number", "required": False}
            ],
            "sla": {"p50_ms": 1500, "p99_ms": 6000},
            "proofs": ["invoice_id", "hosted_invoice_url"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.01},
            "tags": ["payment", "stripe", "invoice"]
        },

        # ====== STORAGE ======
        {
            "name": "storage.upload",
            "connector": "storage",
            "action": "upload_file",
            "description": "Upload file to S3/GCS storage",
            "inputs": [
                {"key": "key", "type": "string", "required": True},
                {"key": "content", "type": "string", "required": True},
                {"key": "content_type", "type": "string", "required": False}
            ],
            "sla": {"p50_ms": 500, "p99_ms": 3000},
            "proofs": ["storage_url", "content_hash"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.00001},
            "tags": ["storage", "file"]
        },

        # ====== AIRTABLE ======
        {
            "name": "airtable.create_record",
            "connector": "airtable",
            "action": "create_record",
            "description": "Create a record in Airtable",
            "inputs": [
                {"key": "table", "type": "string", "required": True},
                {"key": "fields", "type": "object", "required": True}
            ],
            "sla": {"p50_ms": 600, "p99_ms": 3000},
            "proofs": ["record_id"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.001},
            "tags": ["database", "airtable"]
        },

        # ====== HTTP/WEBHOOK ======
        {
            "name": "http.post",
            "connector": "http_generic",
            "action": "http_post",
            "description": "Make HTTP POST request to any API",
            "inputs": [
                {"key": "url", "type": "string", "required": True},
                {"key": "body", "type": "object", "required": False},
                {"key": "headers", "type": "object", "required": False}
            ],
            "sla": {"p50_ms": 500, "p99_ms": 5000},
            "proofs": ["http_response", "status_code"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.001},
            "fallback_connector": "headless",
            "tags": ["http", "api"]
        },
        {
            "name": "webhook.deliver",
            "connector": "webhook",
            "action": "webhook_send",
            "description": "Deliver webhook to URL",
            "inputs": [
                {"key": "url", "type": "string", "required": True},
                {"key": "payload", "type": "object", "required": True}
            ],
            "sla": {"p50_ms": 300, "p99_ms": 2000},
            "proofs": ["delivery_status", "signature"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.0001},
            "tags": ["webhook", "event"]
        },

        # ====== HEADLESS BROWSER ======
        {
            "name": "browser.fill_form",
            "connector": "headless",
            "action": "fill_form",
            "description": "Fill and submit a web form",
            "inputs": [
                {"key": "url", "type": "string", "required": True},
                {"key": "fields", "type": "object", "required": True},
                {"key": "submit_selector", "type": "string", "required": False}
            ],
            "sla": {"p50_ms": 5000, "p99_ms": 30000},
            "proofs": ["screenshot", "final_url"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.02},
            "tags": ["browser", "form", "automation"]
        },
        {
            "name": "browser.scrape",
            "connector": "headless",
            "action": "scrape_content",
            "description": "Scrape content from a web page",
            "inputs": [
                {"key": "url", "type": "string", "required": True},
                {"key": "selectors", "type": "object", "required": True}
            ],
            "sla": {"p50_ms": 3000, "p99_ms": 15000},
            "proofs": ["html_content", "extracted_data"],
            "cost_model": {"type": "per_call", "unit_cost_usd": 0.01},
            "tags": ["browser", "scrape", "data_extraction"]
        }
    ]


# Convenience function
def load_pdl(name: str, catalog: Optional[PDLCatalog] = None) -> Optional[PDLSpec]:
    """Load a PDL by name from default or provided catalog"""
    if catalog is None:
        catalog = PDLCatalog()
        catalog.load_builtin()
    return catalog.get(name)
