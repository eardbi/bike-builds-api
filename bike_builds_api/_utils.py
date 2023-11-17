# --------------------------------------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------------------------------------

from typing import *
from pathlib import Path

import pydantic

# --------------------------------------------------------------------------------------------------
# Exports
# --------------------------------------------------------------------------------------------------

__all__ = [
]

# --------------------------------------------------------------------------------------------------
# Module Variables
# --------------------------------------------------------------------------------------------------

_K = TypeVar('_K')
_V = TypeVar('_V')


# --------------------------------------------------------------------------------------------------
# Classes
# --------------------------------------------------------------------------------------------------

class DictRootModel(pydantic.RootModel[dict[_K, _V]], Generic[_K, _V]):
    root: dict[_K, _V]

    def __iter__(self) -> Iterator[_K]:
        return iter(self.keys())

    def __getitem__(
          self,
          key: _K
    ) -> _V:
        return self.root[key]

    def __getattr__(self, item: str) -> Any:
        return getattr(self.root, item)

    def keys(
          self
    ) -> KeysView[_K]:
        return self.root.keys()

    def values(
          self
    ) -> ValuesView[_V]:
        return self.root.values()

    def items(
          self
    ) -> ItemsView[_K, _V]:
        return self.root.items()

