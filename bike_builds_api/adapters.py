# --------------------------------------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------------------------------------

import pydantic

from bike_builds_api.model import (
    ID,
    Part,
    Manufacturer,
    Shop,
    ScrapeResult,
)

# --------------------------------------------------------------------------------------------------
# Exports
# --------------------------------------------------------------------------------------------------

__all__ = [
    'ItemsType',
    'ItemsAdapter',
    'ScrapeResultsType',
    'ScrapeResultsAdapter',
]

# --------------------------------------------------------------------------------------------------
# Inferred Types
# --------------------------------------------------------------------------------------------------

_BaseItemType = Part | Manufacturer | Shop
ItemsType = _BaseItemType | list[_BaseItemType]
ItemsAdapter = pydantic.TypeAdapter(_BaseItemType | list[_BaseItemType])

ScrapeResultsType = ScrapeResult | list[ScrapeResult] | dict[ID, list[ScrapeResult]]
ScrapeResultsAdapter = pydantic.TypeAdapter(ScrapeResultsType)
