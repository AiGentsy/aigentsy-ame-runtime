"""
SPEC IMPORTER
=============

Auto-generate PDLs from OpenAPI/HAR/Postman specs.
Overnight you add hundreds of endpoints to the UCB with no human time.

Supports:
- OpenAPI 3.x specs
- HAR (HTTP Archive) files
- Postman collections
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import re
import hashlib


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _slugify(s: str) -> str:
    """Convert string to slug"""
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


class SpecImporter:
    """
    Import API specifications and generate PDLs.

    PDL = Protocol Description Language
    Defines how to execute an outcome via a specific connector.
    """

    def __init__(self):
        self._imported: List[Dict[str, Any]] = []
        self._pdls_generated: List[Dict[str, Any]] = []

    def import_spec(self, spec: Dict[str, Any], spec_type: str = "openapi") -> Dict[str, Any]:
        """
        Import a spec and generate PDLs.

        Args:
            spec: The specification dict
            spec_type: openapi, har, or postman

        Returns:
            Import result with PDLs generated
        """
        if spec_type == "openapi":
            return self.import_openapi(spec)
        elif spec_type == "har":
            return self.import_har(spec)
        elif spec_type == "postman":
            return self.import_postman(spec)
        else:
            return {"ok": False, "error": f"unknown_spec_type:{spec_type}"}

    def import_openapi(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import OpenAPI 3.x specification.

        Generates PDL for each endpoint.
        """
        info = spec.get("info", {})
        service_name = _slugify(info.get("title", "unknown_service"))
        base_url = ""

        # Get server URL
        servers = spec.get("servers", [])
        if servers:
            base_url = servers[0].get("url", "")

        paths = spec.get("paths", {})
        pdls = []

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "patch", "delete"]:
                    pdl = self._openapi_endpoint_to_pdl(
                        service_name=service_name,
                        base_url=base_url,
                        path=path,
                        method=method.upper(),
                        details=details
                    )
                    pdls.append(pdl)
                    self._pdls_generated.append(pdl)

        self._imported.append({
            "type": "openapi",
            "service": service_name,
            "imported_at": _now_iso(),
            "pdls_count": len(pdls)
        })

        return {
            "ok": True,
            "service": service_name,
            "pdls_added": len(pdls),
            "pdls": pdls
        }

    def _openapi_endpoint_to_pdl(
        self,
        service_name: str,
        base_url: str,
        path: str,
        method: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert OpenAPI endpoint to PDL"""
        operation_id = details.get("operationId") or f"{method.lower()}_{_slugify(path)}"
        summary = details.get("summary", "")
        description = details.get("description", "")

        # Extract parameters
        parameters = []
        for param in details.get("parameters", []):
            parameters.append({
                "name": param.get("name"),
                "in": param.get("in"),  # query, path, header
                "required": param.get("required", False),
                "type": param.get("schema", {}).get("type", "string")
            })

        # Extract request body schema
        request_body = None
        if "requestBody" in details:
            content = details["requestBody"].get("content", {})
            if "application/json" in content:
                request_body = content["application/json"].get("schema", {})

        # Extract response schema
        response_schema = None
        responses = details.get("responses", {})
        for status, response in responses.items():
            if status.startswith("2"):
                content = response.get("content", {})
                if "application/json" in content:
                    response_schema = content["application/json"].get("schema", {})
                    break

        pdl = {
            "pdl_id": f"{service_name}_{operation_id}",
            "service": service_name,
            "name": operation_id,
            "description": summary or description,
            "connector": "http",
            "method": method,
            "url": f"{base_url}{path}",
            "parameters": parameters,
            "request_body": request_body,
            "response_schema": response_schema,
            "auth_type": self._detect_auth_type(details),
            "rate_limit": self._estimate_rate_limit(details),
            "generated_at": _now_iso(),
            "source": "openapi"
        }

        return pdl

    def _detect_auth_type(self, details: Dict[str, Any]) -> str:
        """Detect authentication type from endpoint details"""
        security = details.get("security", [])
        if not security:
            return "none"

        for sec in security:
            if "bearerAuth" in sec or "Bearer" in str(sec):
                return "bearer"
            if "apiKey" in sec or "api_key" in str(sec):
                return "api_key"
            if "oauth" in str(sec).lower():
                return "oauth2"
            if "basic" in str(sec).lower():
                return "basic"

        return "unknown"

    def _estimate_rate_limit(self, details: Dict[str, Any]) -> Dict[str, int]:
        """Estimate rate limits (conservative defaults)"""
        return {
            "requests_per_minute": 60,
            "requests_per_day": 10000
        }

    def import_har(self, har: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import HAR (HTTP Archive) file.

        HAR files capture actual HTTP traffic, useful for reverse engineering APIs.
        """
        log = har.get("log", {})
        entries = log.get("entries", [])

        # Group by domain
        by_domain: Dict[str, List] = {}
        for entry in entries:
            request = entry.get("request", {})
            url = request.get("url", "")

            # Extract domain
            match = re.match(r'https?://([^/]+)', url)
            if match:
                domain = match.group(1)
                if domain not in by_domain:
                    by_domain[domain] = []
                by_domain[domain].append(entry)

        pdls = []
        for domain, domain_entries in by_domain.items():
            service_name = _slugify(domain.split('.')[0])

            for entry in domain_entries:
                pdl = self._har_entry_to_pdl(service_name, entry)
                if pdl:
                    pdls.append(pdl)
                    self._pdls_generated.append(pdl)

        self._imported.append({
            "type": "har",
            "domains": list(by_domain.keys()),
            "imported_at": _now_iso(),
            "pdls_count": len(pdls)
        })

        return {
            "ok": True,
            "domains": list(by_domain.keys()),
            "pdls_added": len(pdls),
            "pdls": pdls
        }

    def _har_entry_to_pdl(self, service_name: str, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert HAR entry to PDL"""
        request = entry.get("request", {})
        response = entry.get("response", {})

        method = request.get("method", "GET")
        url = request.get("url", "")

        # Skip non-API requests
        if any(ext in url for ext in [".js", ".css", ".png", ".jpg", ".gif", ".ico", ".woff"]):
            return None

        # Extract path
        match = re.match(r'https?://[^/]+(.*)', url)
        path = match.group(1) if match else url

        # Generate operation ID from path
        operation_id = _slugify(f"{method.lower()}_{path}")

        # Extract headers
        headers = {h["name"]: h["value"] for h in request.get("headers", [])}

        # Extract query params
        query_params = []
        for qs in request.get("queryString", []):
            query_params.append({
                "name": qs.get("name"),
                "in": "query",
                "required": False,
                "type": "string"
            })

        # Extract request body
        request_body = None
        post_data = request.get("postData", {})
        if post_data.get("text"):
            try:
                request_body = json.loads(post_data["text"])
            except:
                request_body = {"raw": post_data.get("text")}

        pdl = {
            "pdl_id": f"{service_name}_{operation_id[:50]}",
            "service": service_name,
            "name": operation_id[:50],
            "description": f"Captured from HAR: {method} {path[:100]}",
            "connector": "http",
            "method": method,
            "url": url.split("?")[0],  # Remove query string
            "parameters": query_params,
            "request_body": request_body,
            "headers": {k: v for k, v in headers.items() if k.lower() not in ["cookie", "authorization"]},
            "auth_type": "bearer" if "authorization" in [h.lower() for h in headers] else "none",
            "rate_limit": {"requests_per_minute": 30, "requests_per_day": 5000},
            "generated_at": _now_iso(),
            "source": "har"
        }

        return pdl

    def import_postman(self, collection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import Postman collection.
        """
        info = collection.get("info", {})
        service_name = _slugify(info.get("name", "postman_collection"))

        items = collection.get("item", [])
        pdls = []

        def process_items(items, prefix=""):
            for item in items:
                if "item" in item:
                    # Folder
                    folder_name = item.get("name", "")
                    process_items(item["item"], f"{prefix}{_slugify(folder_name)}_")
                elif "request" in item:
                    # Request
                    pdl = self._postman_item_to_pdl(service_name, item, prefix)
                    if pdl:
                        pdls.append(pdl)
                        self._pdls_generated.append(pdl)

        process_items(items)

        self._imported.append({
            "type": "postman",
            "service": service_name,
            "imported_at": _now_iso(),
            "pdls_count": len(pdls)
        })

        return {
            "ok": True,
            "service": service_name,
            "pdls_added": len(pdls),
            "pdls": pdls
        }

    def _postman_item_to_pdl(
        self,
        service_name: str,
        item: Dict[str, Any],
        prefix: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Convert Postman item to PDL"""
        request = item.get("request", {})
        name = item.get("name", "unnamed")

        method = request.get("method", "GET")

        # Handle URL (can be string or object)
        url_data = request.get("url", {})
        if isinstance(url_data, str):
            url = url_data
        else:
            raw = url_data.get("raw", "")
            url = raw

        operation_id = f"{prefix}{_slugify(name)}"

        # Extract query params
        query_params = []
        if isinstance(url_data, dict):
            for q in url_data.get("query", []):
                query_params.append({
                    "name": q.get("key"),
                    "in": "query",
                    "required": False,
                    "type": "string"
                })

        # Extract body
        request_body = None
        body = request.get("body", {})
        if body.get("mode") == "raw":
            try:
                request_body = json.loads(body.get("raw", "{}"))
            except:
                request_body = {"raw": body.get("raw")}

        # Extract headers
        headers = {}
        for h in request.get("header", []):
            if h.get("key", "").lower() not in ["authorization", "cookie"]:
                headers[h.get("key")] = h.get("value")

        pdl = {
            "pdl_id": f"{service_name}_{operation_id[:50]}",
            "service": service_name,
            "name": name,
            "description": item.get("description", f"Postman: {name}"),
            "connector": "http",
            "method": method,
            "url": url.split("?")[0],
            "parameters": query_params,
            "request_body": request_body,
            "headers": headers,
            "auth_type": "bearer" if any(h.get("key", "").lower() == "authorization" for h in request.get("header", [])) else "none",
            "rate_limit": {"requests_per_minute": 60, "requests_per_day": 10000},
            "generated_at": _now_iso(),
            "source": "postman"
        }

        return pdl

    def get_pdl(self, pdl_id: str) -> Optional[Dict[str, Any]]:
        """Get generated PDL by ID"""
        for pdl in self._pdls_generated:
            if pdl.get("pdl_id") == pdl_id:
                return pdl
        return None

    def list_pdls(self, service: str = None) -> List[Dict[str, Any]]:
        """List generated PDLs"""
        pdls = self._pdls_generated
        if service:
            pdls = [p for p in pdls if p.get("service") == service]
        return pdls

    def get_stats(self) -> Dict[str, Any]:
        """Get importer statistics"""
        by_source = {}
        for pdl in self._pdls_generated:
            source = pdl.get("source", "unknown")
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total_imports": len(self._imported),
            "total_pdls": len(self._pdls_generated),
            "by_source": by_source
        }


# Module-level singleton
_spec_importer = SpecImporter()


def import_openapi(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Import OpenAPI spec"""
    return _spec_importer.import_openapi(spec)


def import_har(har: Dict[str, Any]) -> Dict[str, Any]:
    """Import HAR file"""
    return _spec_importer.import_har(har)


def import_postman(collection: Dict[str, Any]) -> Dict[str, Any]:
    """Import Postman collection"""
    return _spec_importer.import_postman(collection)


def get_imported_pdls(service: str = None) -> List[Dict[str, Any]]:
    """Get imported PDLs"""
    return _spec_importer.list_pdls(service)
