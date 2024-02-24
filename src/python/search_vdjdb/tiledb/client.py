"""TileDB Cloud client."""

import os
from typing import Callable, Any

import tiledb
import tiledb.cloud
from attrs import define, field
from pydantic.dataclasses import dataclass as pydantic_dataclass

from search_vdjdb.di_container import DiContainer


@pydantic_dataclass(frozen=True)
class ObjectRegistration:
    """Object registration metadata for TileDB Cloud."""

    name: str
    """Name of the object to register."""
    executable: Callable
    """Executable function to register."""


@define
class TiledbClient:
    """Base client for TileDB Cloud."""

    api_token: str = field()
    """API token for TileDB Cloud."""

    @api_token.default
    def _api_token_default(self) -> str:
        return os.environ["TILEDB_TOKEN"]

    di: DiContainer = field(init=False, factory=DiContainer)
    """Dependency injection container."""


@pydantic_dataclass(frozen=True)
class UdfInput:
    """Input for UDF."""

    name: str
    """Name of the UDF task."""
    udf: Callable
    """UDF to run."""
    args: list = field(factory=list)
    """Positional arguments for UDF."""


@define
class UdfClient(TiledbClient):
    """UDF client for TileDB Cloud."""

    def register_udf(self, obj: ObjectRegistration) -> None:
        """Register UDF to TileDB Cloud."""

        tiledb.cloud.udf.register_generic_udf(obj.executable, name=obj.name)

    def run_udf(self, input: UdfInput) -> Any:
        """Run UDF on TileDB Cloud."""

        response = tiledb.cloud.udf.exec(input.udf, *input.args)

        return response
