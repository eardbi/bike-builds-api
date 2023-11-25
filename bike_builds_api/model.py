# --------------------------------------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------------------------------------

from typing import *
from typing_extensions import Self
import datetime
import abc
import re
from enum import Enum

import pydantic
import pydantic.functional_serializers

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
    'ProductPricing',
    'NamedBaseModel',
    'CollectionName',
    'ComponentID',
    'Shop',
    'Listing',
    'Manufacturer',
    'Variant',
    'Part',
    'ScrapeField',
    'PageScrapeConfig',
    'ScrapeResult',
    'Variables',
    'Item',
    'COMPONENT_NAME_MAP',
]


# --------------------------------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------------------------------

class Currency(str, Enum):
    EUR = 'EUR'
    USD = 'USD'
    GBP = 'GBP'
    CHF = 'CHF'


class CollectionName(str, Enum):
    PARTS = 'parts'
    MANUFACTURERS = 'manufacturers'
    SHOPS = 'shops'
    PRICES = 'prices'


class ComponentID(str, Enum):
    BOTTOM_BRACKET = 'bottom_bracket'
    BRAKE = 'brake'
    CASSETTE = 'cassette'
    CHAIN = 'chain'
    CHAINRING = 'chainring'
    CRANKSET = 'crankset'
    DERAILLEUR = 'derailleur'
    FENDER = 'fender'
    FORK = 'fork'
    FRAME = 'frame'
    HANDLEBAR = 'handlebar'
    HEADSET = 'headset'
    HUB = 'hub'
    PEDAL = 'pedal'
    RIM = 'rim'
    SADDLE = 'saddle'
    SEATPOST = 'seatpost'
    SHOCK = 'shock'
    STEM = 'stem'
    TIRE = 'tire'
    TOOL = 'tool'
    TRIGGER = 'trigger'
    WHEEL = 'wheel'

    SPARE_PARTS = 'spare_parts'
    OTHER = 'other'


# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------

_ID_CHARACTERS = r'a-z0-9_'
_ID_PATTERN = rf'^[{_ID_CHARACTERS}]+$'
_NON_ID_CHARACTERS_PATTERN = rf'[^{_ID_CHARACTERS}]'

COMPONENT_NAME_MAP = {
    ComponentID.FRAME:          'Frame',
    ComponentID.FORK:           'Fork',
    ComponentID.HEADSET:        'Headset',
    ComponentID.SHOCK:          'Shock',
    ComponentID.BOTTOM_BRACKET: 'Bottom Bracket',
    ComponentID.WHEEL:          'Wheel',
    ComponentID.TIRE:           'Tire',
    ComponentID.TRIGGER:        'Trigger',
    ComponentID.HANDLEBAR:      'Handlebar',
    ComponentID.STEM:           'Stem',
    ComponentID.SEATPOST:       'Seatpost',
    ComponentID.SADDLE:         'Saddle',
    ComponentID.CRANKSET:       'Crankset',
    ComponentID.CHAINRING:      'Chainring',
    ComponentID.CHAIN:          'Chain',
    ComponentID.CASSETTE:       'Cassette',
    ComponentID.DERAILLEUR:     'Derailleur',
    ComponentID.BRAKE:          'Brake',
    ComponentID.PEDAL:          'Pedal',
    ComponentID.FENDER:         'Fender',
    ComponentID.TOOL:           'Tool',
    ComponentID.HUB:            'Hub',
    ComponentID.RIM:            'Rim',

    ComponentID.SPARE_PARTS:    'Spare Parts',
    ComponentID.OTHER:          'Other',
}

# --------------------------------------------------------------------------------------------------
# Types
# --------------------------------------------------------------------------------------------------

ID = Annotated[str, pydantic.StringConstraints(pattern=_ID_PATTERN)]
Rating = Annotated[pydantic.NonNegativeInt, pydantic.Field(le=5)]
URL = Annotated[
    pydantic.HttpUrl,
    pydantic.functional_serializers.PlainSerializer(
        lambda x: x.unicode_string(),
        str
    )
]


# --------------------------------------------------------------------------------------------------
# Base Models
# --------------------------------------------------------------------------------------------------

class _BaseModel(
    pydantic.BaseModel, abc.ABC,
    extra='forbid',
    validate_assignment=True,
):
    pass


class NamedBaseModel(_BaseModel, abc.ABC):
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


# class CollectionBaseModel(NamedBaseModel, abc.ABC):
#     _collection: CollectionName
#     # TODO(schmuck): should this be removed again?
#     # TODO(schmuck): can collection be made a private field and used in a union discriminator?
#     collection: CollectionName


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
    price: Price | None = None  # TODO(schmuck): this should be necessary
    discount: bool | None = None
    available: bool | None = None
    rating: Rating | None = None  # TODO(schmuck): Add rating model


class ProductPricing(_BaseModel):
    timestamp: datetime.date

    part_id: ID
    variant_id: ID
    shop_id: ID

    price_tag: PriceTag


# Parts
# --------------------------------------------------------------------------------------------------

# TODO(schmuck): do some renaming here, part/variant/variables is too generic
class Variables(_BaseModel):
    part: str
    # variant: str | None = None  # TODO(schmuck): What is this actually gonna be?


class Listing(_BaseModel):
    last_modified: Annotated[
        datetime.datetime,
        pydantic.Field(default_factory=datetime.datetime.utcnow)
    ]

    url: URL | None = None  # TODO(schmuck): should this be required?

    name: str | None = None
    manufacturer: str | None = None

    price_tag: PriceTag

    # scrape_provider: str
    variables: Variables | None = None  # TODO(schmuck): is this solvable differently?


class Variant(NamedBaseModel):
    year: int | None = None
    product_code: str | None = None
    on_wish_list: bool = False

    listings: dict[ID, Listing] = None


class Part(NamedBaseModel):
    _collection = CollectionName.PARTS

    # collection: Literal[CollectionName.PARTS] = CollectionName.PARTS

    component: ComponentID
    manufacturer_id: ID

    variants: list[Variant] = []

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

class Manufacturer(NamedBaseModel):
    _collection = CollectionName.MANUFACTURERS

    # collection: Literal[CollectionName.MANUFACTURERS] = CollectionName.MANUFACTURERS
    url: URL = None


# Shop
# --------------------------------------------------------------------------------------------------

class ScrapeFields(_BaseModel, abc.ABC):
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


class PartScrapeFields(ScrapeFields):
    price: ScrapeField

    # variant: ScrapeField | None = None


class SearchScrapeFields(ScrapeFields):
    part: ScrapeField


class PageScrapeConfig(_BaseModel, abc.ABC):
    _URL_VARIABLES: ClassVar

    # TODO(schmuck): add an optional index here which should also be available all the way to the endpoint to not
    #  waste bandwidth
    url_extra: str
    fields: ScrapeFields

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


class PartScrapeConfig(PageScrapeConfig):
    _URL_VARIABLES: ClassVar = ('part', 'variant')

    fields: PartScrapeFields


class SearchScrapeConfig(PageScrapeConfig):
    _URL_VARIABLES: ClassVar = ('query',)

    fields: SearchScrapeFields


# TODO(schmuck): all the parts and variants is a bit confusing, consider renaming

class PartScrapeConfigs(_BaseModel):
    part: PartScrapeConfig
    # variant: PartScrapeConfig | None = None


class ScraperConfig(_BaseModel):
    mode: Literal['browser', 'headless']
    part: PartScrapeConfigs
    search: SearchScrapeConfig


class Shop(NamedBaseModel):
    # TODO(schmuck): This can move down to the backend core base
    _collection = CollectionName.SHOPS

    # collection: Literal[CollectionName.SHOPS] = CollectionName.SHOPS

    url: URL
    scraper_config: ScraperConfig

    currency: Currency
    mwst: float | None = None  # TODO(schmuck): make this required as soon as all shops have it
    shipping_cost: float | None = None  # same as above


# Scraper
# --------------------------------------------------------------------------------------------------

class ScrapeResult(_BaseModel):
    name: str | None = None
    manufacturer: str | None = None

    price: float | None = None
    discount: bool | None = None
    available: bool | None = None
    rating: Rating | None = None

    part: str | None = None
    # variant: str | None = None


# --------------------------------------------------------------------------------------------------
# Inferred Types
# --------------------------------------------------------------------------------------------------

# TODO(schmuck): don't use discriminated unions
Item = Part | Manufacturer | Shop

# # --------------------------------------------------------------------------------------------------
# # Compile Time Assertions
# # --------------------------------------------------------------------------------------------------
#
# assert set(SearchScrapeFields.model_fields) == set(ScrapeResult.model_fields), \
#     "Scrape fields must match the scrape result fields!"
