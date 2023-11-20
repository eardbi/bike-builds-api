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


class ComponentName(str, Enum):
    FRAME = 'frame'
    FORK = 'fork'
    HEADSET = 'headset'
    SHOCK = 'shock'
    BOTTOM_BRACKET = 'bottom_bracket'
    WHEEL = 'wheel'
    TIRE = 'tire'
    TRIGGER = 'trigger'
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
    HUB = 'hub'
    OTHER = 'other'


# --------------------------------------------------------------------------------------------------
# Base Models
# --------------------------------------------------------------------------------------------------

class _BaseModel(
    pydantic.BaseModel, abc.ABC,
    extra='forbid',
):
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
    # TODO(schmuck): should this be removed again?
    # TODO(schmuck): can collection be made a private field and used in a union discriminator?
    collection: CollectionName


# --------------------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------------------

# Price
# --------------------------------------------------------------------------------------------------

class Price(_BaseModel):
    value: float
    currency: str


class PriceTag(
    _BaseModel, abc.ABC,
    extra='ignore',
):
    price: Price | None = None  # TODO(schmuck): is the currency really necessary? it can be inferred from the shop
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
    year: int | None = None
    product_code: str | None = None
    on_wish_list: bool = False
    listings: list[Listing] = []


class Part(_CollectionBaseModel):
    collection: Literal[CollectionName.PARTS] = CollectionName.PARTS
    component: ComponentName
    manufacturer_id: ID
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


class ScrapeFields(_BaseModel, validate_default=True):
    part: ScrapeField | None = None
    variant: ScrapeField | None = None
    name: ScrapeField | None = None
    manufacturer: ScrapeField | None = None
    price: ScrapeField | None = None
    available: ScrapeField | None = None
    rating: ScrapeField | None = None
    discount: ScrapeField | None = None

    @pydantic.model_validator(mode='after')
    def validate_at_least_one_target(
          self
    ):
        assert any(
            getattr(self, field) is not None
            for field in self.model_fields
        ), "At least one scrape target must be specified!"

        return self


class PageScraperConfig(_BaseModel):
    _URL_VARIABLES: ClassVar = ('part', 'variant')

    # TODO(schmuck): add an optional index here which should also be available all the way to the endpoint to not
    #  waste bandwidth
    url_extra: str
    fields: ScrapeFields | None = None

    @pydantic.field_validator('url_extra')
    @classmethod
    def validate_url_extra(
          cls,
          v: str,
          info: pydantic.ValidationInfo
    ):
        results = re.findall(r'{(.*?)}', v)
        assert results, f"URL extra '{v}' does not contain any variables!"

        for match in results:
            assert match in cls._URL_VARIABLES, \
                f"URL extra '{v}' contains invalid variable '{match}'!"

        return v


class SearchScraperConfig(PageScraperConfig):
    _URL_VARIABLES: ClassVar = ('query',)


class ScraperConfig(_BaseModel):
    mode: Literal['browser', 'headless']
    part: dict[str, PageScraperConfig]
    search: SearchScraperConfig


class Shop(_CollectionBaseModel):
    collection: Literal[CollectionName.SHOPS] = CollectionName.SHOPS
    url: pydantic.HttpUrl
    mwst: float | None = None  # TODO(schmuck): make this required as soon as all shops have it
    shipping_cost: float | None = None  # same as above
    currency: Literal['EUR', 'USD', 'GBP', 'CHF']
    scraper_config: ScraperConfig


# Scraper
# --------------------------------------------------------------------------------------------------

class ScrapeResult(PriceTag, validate_default=True):
    name: str | None = None
    manufacturer: str | None = None
    part: str | None = None
    variant: str | None = None


# --------------------------------------------------------------------------------------------------
# Inferred Types
# --------------------------------------------------------------------------------------------------

Item = Annotated[
    Part | Manufacturer | Shop,
    pydantic.Field(
        discriminator='collection',
    )
]

# --------------------------------------------------------------------------------------------------
# Compile Time Assertions
# --------------------------------------------------------------------------------------------------

assert set(ScrapeFields.model_fields) == set(ScrapeResult.model_fields), \
    "Scrape fields must match the scrape result fields!"
