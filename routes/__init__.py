"""
ROUTES - FastAPI Route Modules
==============================

Public-facing API routes for proofs, catalog, and operational endpoints.
"""

# Import routers when FastAPI is available
try:
    from .public_proofs import router as proofs_router
    from .catalog_sitemap import router as sitemap_router
    __all__ = ["proofs_router", "sitemap_router"]
except ImportError:
    # FastAPI not installed - provide stubs
    proofs_router = None
    sitemap_router = None
    __all__ = []
