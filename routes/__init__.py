"""
ROUTES - FastAPI Route Modules
==============================

Public-facing API routes for proofs, catalog, operational, Access Panel, and Integration endpoints.
"""

# Import routers when FastAPI is available
try:
    from .public_proofs import router as proofs_router
    from .catalog_sitemap import router as sitemap_router
    from .access_panel import get_access_panel_router
    from .integration_routes import get_integration_router
    __all__ = ["proofs_router", "sitemap_router", "get_access_panel_router", "get_integration_router"]
except ImportError:
    # FastAPI not installed - provide stubs
    proofs_router = None
    sitemap_router = None
    def get_access_panel_router(): return None
    def get_integration_router(): return None
    __all__ = []
