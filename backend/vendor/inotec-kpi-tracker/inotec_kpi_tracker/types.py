from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

VALID_CATEGORIES = frozenset({
    "usage", "performance", "engagement", "business_impact", "security"
})


@dataclass
class KPIEvent:
    app_id: str
    event_type: str
    category: str
    kpi_id: str
    value: float
    unit: str = "count"
    environment: str = "production"
    session_id: str = "server"
    dimensions: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.category not in VALID_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(VALID_CATEGORIES)}, got '{self.category}'"
            )

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "app_id": self.app_id,
            "environment": self.environment,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "category": self.category,
            "kpi_id": self.kpi_id,
            "value": self.value,
            "unit": self.unit,
            "session_id": self.session_id,
        }
        if self.dimensions is not None:
            d["dimensions"] = self.dimensions
        if self.metadata is not None:
            d["metadata"] = self.metadata
        return d


@dataclass
class KPIConfig:
    api_url: str
    api_key: str
    app_id: str
    environment: str = "production"
    batch_size: int = 50
    flush_interval: float = 10.0  # seconds


@dataclass
class SyncKPIConfig:
    api_url: str
    api_key: str
    app_id: str
    environment: str = "production"
    batch_size: int = 50
    flush_interval: float = 10.0  # seconds
