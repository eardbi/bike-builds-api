# --------------------------------------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------------------------------------

from typing import *
from typing_extensions import Self
import abc
import re
from enum import Enum

import pydantic

from scrape_api import (
    ScrapeField,
)

# --------------------------------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------------------------------

__all__ = [
    'ID',
    'Price',
    'PriceTag',
    'NamedBaseModel',
    'CollectionName',
    'Shop',
    'Manufacturer',
    'Part',
    'ScrapeField',
    'ScrapeResult',
    'ScrapeTargetName',
    'Item',
]

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------

_ID_CHARACTERS = r'a-z0-9_'
_ID_PATTERN = rf'^[{_ID_CHARACTERS}]+$'
_NON_ID_CHARACTERS_PATTERN = rf'[^{_ID_CHARACTERS}]'

# --------------------------------------------------------------------------------------------------
# Types
# --------------------------------------------------------------------------------------------------

ID = Annotated[str, pydantic.StringConstraints(pattern=_ID_PATTERN)]
Rating = Annotated[pydantic.NonNegativeInt, pydantic.Field(le=5)]


# --------------------------------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------------------------------

class CollectionName(str, Enum):
    PARTS = 'parts'
    MANUFACTURERS = 'manufacturers'
    SHOPS = 'shops'
    PRICES = 'prices'


class ScrapeTargetName(str, Enum):
    URL = 'url'
    NAME = 'name'
    MANUFACTURER = 'manufacturer'
    PRICE = 'price'
    AVAILABLE = 'available'
    RATING = 'rating'
    DISCOUNT = 'discount'


class ComponentName(str, Enum):
    FRAME = 'frame'
    FORK = 'fork'
    HEADSET = 'headset'
    SHOCK = 'shock'
    BOTTOM_BRACKET = 'bottom_bracket'
    WHEEL = 'wheel'
    TIRE = 'tire'
    HANDLEBAR = 'handlebar'
    STEM = 'stem'
    SEATPOST = 'seatpost'
    SADDLE = 'saddle'
    CRANKSET = 'crankset'
    CHAINRING = 'chainring'
    CHAIN = 'chain'
    CASSETTE = 'cassette'
    DERAILLEUR = 'derailleur'
    BRAKE = 'brake'
    PEDAL = 'pedal'
    FENDER = 'fender'
    TOOL = 'tool'
    OTHER = 'other'


# --------------------------------------------------------------------------------------------------
# Base Models
# --------------------------------------------------------------------------------------------------

class _BaseModel(pydantic.BaseModel, abc.ABC):
    pass


class NamedBaseModel(_BaseModel, abc.ABC, ):
    name: Annotated[
        str,
        pydantic.Field(
            min_length=1,
            max_length=200
        )
    ]
    id: Annotated[
        ID | None,
        pydantic.Field(
            validate_default=True
        )
    ] = None

    @staticmethod
    def id_from_name(
          name: str
    ) -> ID:
        return (
            name.lower()
            .replace(' ', '_')
            .replace('-', '_')
            .replace('.', '_')
        )

    @pydantic.model_validator(mode='after')
    def infer_id(self):
        if self.id is not None:
            return self

        # Infer ID from name
        self.id = re.sub(
            _NON_ID_CHARACTERS_PATTERN, '',
            self.id_from_name(self.name)
        )

        return self


class _CollectionBaseModel(NamedBaseModel, abc.ABC):
    collection: CollectionName


# --------------------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------------------

# Price
# --------------------------------------------------------------------------------------------------

class Price(_BaseModel):
    value: float
    currency: str


class PriceTag(_BaseModel, abc.ABC):
    price: Price | None = None
    available: bool | None = None
    rating: Rating | None = None  # TODO(schmuck): Add rating model
    discount: bool | None = None


# Parts
# --------------------------------------------------------------------------------------------------

class Listing(_BaseModel):
    shop_id: ID
    provider: str
    variables: Annotated[
        dict[str, str],
        pydantic.Field(min_length=1)
    ]
    price_tag: PriceTag | None = None


class PartVariant(NamedBaseModel):
    listings: list[Listing] = []


class Part(_CollectionBaseModel):
    collection: Literal[CollectionName.PARTS] = CollectionName.PARTS
    component: ComponentName
    manufacturer_id: ID
    year: int | None = None
    variants: list[PartVariant] = []

    @pydantic.model_validator(mode='after')
    def infer_id(self):
        if self.id is not None:
            return self

        # Infer ID from name
        self.id = re.sub(
            _NON_ID_CHARACTERS_PATTERN, '',
            f"{self.manufacturer_id}_{self.id_from_name(self.name)}"
        )

        return self


# Manufacturer
# --------------------------------------------------------------------------------------------------

class Manufacturer(_CollectionBaseModel):
    collection: Literal[CollectionName.MANUFACTURERS] = CollectionName.MANUFACTURERS
    url: pydantic.HttpUrl = None


# Shop
# --------------------------------------------------------------------------------------------------

class PageScraperConfig(_BaseModel):
    # TODO(schmuck): add an optional index here which should also be available all the way to the endpoint to not
    #  waste bandwidth
    url_extra: str
    variables: list[str] = []
    fields: dict[ScrapeTargetName, ScrapeField]

    @pydantic.field_validator('url_extra')
    @classmethod
    def validate_url_extra(
          cls,
          v: str,
          info: pydantic.ValidationInfo
    ):
        if 'variables' in info.data:
            for match in re.findall(r'{(.*?)}', v):
                assert match in info.data['variables'], \
                    f"Variable '{match}' not defined in 'variables'!"
        return v


class SearchScraperConfig(PageScraperConfig):
    variables: list[str] = ['query']

    @pydantic.field_validator('variables')
    @classmethod
    def validate_variables(
          cls,
          v: list[str],
    ):
        assert v == ['query'], \
            f"Variables '{v}' must be omitted or contain only 'query'!"
        return v


class ScraperConfig(_BaseModel):
    mode: Literal['browser', 'headless']
    part: dict[str, PageScraperConfig]
    search: SearchScraperConfig


class Shop(_CollectionBaseModel):
    collection: Literal[CollectionName.SHOPS] = CollectionName.SHOPS
    url: pydantic.HttpUrl
    currency: Literal['EUR', 'USD', 'GBP', 'CHF']
    scraper_config: ScraperConfig


# Scraper
# --------------------------------------------------------------------------------------------------

class ScrapeResult(PriceTag):
    url: pydantic.HttpUrl | None = None
    name: str | None = None
    manufacturer: str | None = None

    @pydantic.field_validator('*')
    def validate_field_types(
          cls,
          v: Any,
          info: pydantic.ValidationInfo
    ):
        assert info.field_name in [name for name in ScrapeTargetName], \
            f"Field '{info.field_name}' is not a valid scrape result field!"
        return v


# --------------------------------------------------------------------------------------------------
# Inferred Types
# --------------------------------------------------------------------------------------------------

Item = Annotated[
    Part | Manufacturer | Shop,
    pydantic.Field(
        discriminator='collection',
    )
]
