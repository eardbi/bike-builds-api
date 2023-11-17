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

class _BaseModel(
    pydantic.BaseModel,
    abc.ABC,
    extra='forbid',
):
    pass


class _NonEmptyBaseModel(_BaseModel, abc.ABC):
    @pydantic.model_validator(mode='after')
    def validate_non_empty(self):
        print('---')
        print(self.model_dump())
        assert any(
            value is not None
            for value in self.model_dump().values()
        ), "PriceTag must not be empty!"
        return self


class _OnlyOneBaseModel(_BaseModel, abc.ABC):
    @pydantic.model_validator(mode='after')
    def validate_only_one(self):
        assert sum(
            value is not None
            for value in self.model_dump().values()
        ) == 1, "Only one field must be set!"
        return self


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

    @pydantic.field_validator('id')
    @classmethod
    def infer_id(
          cls,
          v: str,
          info: pydantic.ValidationInfo,
    ) -> ID | None:
        if v is not None:
            return v

        if 'name' not in info.data:
            return None

        # Infer ID from name
        id_from_name = re.sub(
            _NON_ID_CHARACTERS_PATTERN, '',
            cls.id_from_name(info.data['name'])
        )

        # TODO(schmuck): This is a problem when the name is changed
        # # Pre-validate ID
        # if v is not None and v != id_from_name:
        #     raise ValueError(
        #         f"ID '{v}' does not match inferred ID '{id_from_name}'"
        #     )

        return id_from_name


# --------------------------------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------------------------------

# Price
# --------------------------------------------------------------------------------------------------

class Price(_BaseModel):
    value: float
    currency: str


class BasePriceTag(_BaseModel):
    price: Price | None = None
    available: bool | None = None
    rating: Annotated[
        pydantic.NonNegativeInt | None,
        pydantic.Field(le=5)
    ] = None  # TODO(schmuck): Add rating model
    discount: bool | None = None


# Parts
# --------------------------------------------------------------------------------------------------

class Listing(_BaseModel):
    shop_id: ID
    variables: Annotated[
        dict[str, Any],
        pydantic.Field(min_length=1)
    ]


class PartVariant(NamedBaseModel):
    listings: list[Listing] = []


class Part(NamedBaseModel):
    component: ComponentName
    manufacturer_id: ID
    year: int | None = None
    variants: list[PartVariant] = []


# Manufacturer
# --------------------------------------------------------------------------------------------------

class Manufacturer(NamedBaseModel):
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


class Shop(NamedBaseModel):
    url: pydantic.HttpUrl
    currency: Literal['EUR', 'USD', 'GBP', 'CHF']
    scraper_config: ScraperConfig


# Scraper
# --------------------------------------------------------------------------------------------------

class ScrapeResult(_BaseModel):
    url: pydantic.HttpUrl | None = None
    name: str | None = None
    manufacturer: str | None = None
    price: Price | None = None
    available: bool | None = None
    rating: Rating | None = None
    discount: bool | None = None

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

Item = Part | Manufacturer | Shop
