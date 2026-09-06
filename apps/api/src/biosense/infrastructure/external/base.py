"""Common interface for public-data connectors.

Every connector in `infrastructure/external/` wraps a real, verified external API
(see docs/data-access.md) and keeps its own domain-specific methods for actual
application use (e.g. `fetch_cancer_statistics`, `search_and_fetch`,
`search_projects`) — those stay the primary way services call into a connector,
since collapsing five very different APIs into one generic shape would lose
real capability.

`PublicDataConnector` adds a second, uniform surface (`search`/`fetch`/
`health_check`) on top of that, for generic tooling that needs to treat any
connector interchangeably — a connector registry, a health-check dashboard, or
an admin endpoint listing configured sources — without knowing each API's
specific method names.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PublicDataConnector(ABC):
    """Uniform search/fetch/health_check surface implemented by every connector."""

    SOURCE: str

    @abstractmethod
    async def search(self, query: str, filters: dict[str, Any] | None = None) -> list[Any]:
        """Search this source. `filters` is connector-specific (see each implementation)."""

    @abstractmethod
    async def fetch(self, identifier: str) -> Any | None:
        """Fetch a single record by its connector-specific identifier."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the upstream source is currently reachable."""
