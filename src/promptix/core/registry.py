"""Pluggable registry for attack modules and target adapters."""
from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


class Registry(dict[str, type]):
    def register(self, name: str) -> Callable[[type[T]], type[T]]:
        def deco(cls: type[T]) -> type[T]:
            if name in self:
                raise ValueError(f"already registered: {name}")
            self[name] = cls
            return cls
        return deco

    def get_or_raise(self, name: str) -> type:
        if name not in self:
            raise KeyError(f"unknown entry '{name}'. available: {sorted(self)}")
        return self[name]


MODULES: Registry = Registry()
TARGETS: Registry = Registry()
