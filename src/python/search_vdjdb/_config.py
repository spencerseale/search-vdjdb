"""Configuration module for the search_vdjdb package."""

from dataclasses import fields
from typing import Any, Iterator, Mapping, Optional

import toml
from attrs import define, field
from importlib_resources import files
from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass(frozen=True)
class SimpleInput:
    """Simple input format"""

    log_level: str
    query: Optional[str] = None
    output: bool = False

    def __iter__(self) -> Iterator[str]:
        return (getattr(self, field.name) for field in fields(self))


@pydantic_dataclass(frozen=True)
class ValidatedInput:
    log_level: Mapping[str, Any]
    query: Mapping[str, Any]
    output: Mapping[str, Any]

    def __iter__(self) -> Iterator[str]:
        return (getattr(self, field.name) for field in fields(self))


@define
class ArgsConfig:
    """Handles loading of library configurations."""

    configpath: str = "search_vdjdb/configs/args.toml"
    _raw: dict = field(init=False)

    def load(self) -> ValidatedInput:
        cdir, cpath = self.configpath.rsplit("/", 1)
        self._raw = toml.loads(files(cdir.replace("/", ".")).joinpath(cpath).read_text())
        return ValidatedInput(**self._raw)
