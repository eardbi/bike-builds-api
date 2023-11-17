from bike_builds_api.model import *
from bike_builds_api.adapters import *

COLLECTION_MAP = {
    CollectionName.PARTS:         Part,
    CollectionName.MANUFACTURERS: Manufacturer,
    CollectionName.SHOPS:         Shop,
}
