"""
inotec-kpi-tracker — Python SDK for KPI-Tracking

Usage (async / FastAPI):
    from inotec_kpi_tracker import KPIClient, KPIEvent, KPIConfig

Usage (sync / Django):
    from inotec_kpi_tracker import KPISyncClient, KPIEvent, SyncKPIConfig

Middleware:
    from inotec_kpi_tracker import DjangoKPIMiddleware, fastapi_kpi_middleware
"""

from .types import KPIEvent, KPIConfig, SyncKPIConfig
from .client import KPIClient
from .sync_client import KPISyncClient
from .middleware import DjangoKPIMiddleware, fastapi_kpi_middleware

__version__ = "1.0.0"
__all__ = [
    "KPIEvent",
    "KPIConfig",
    "SyncKPIConfig",
    "KPIClient",
    "KPISyncClient",
    "DjangoKPIMiddleware",
    "fastapi_kpi_middleware",
    "__version__",
]
