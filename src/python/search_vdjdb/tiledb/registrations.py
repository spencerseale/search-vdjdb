"""Register assets to TileDB Cloud."""

from typing import List, Optional

from search_vdjdb._config import SimpleInput
from search_vdjdb._query import QueryResult
from search_vdjdb.di_container import DiContainer
from search_vdjdb.tiledb.client import ObjectRegistration, UdfClient


def extract_vdjdb(
    di_container: DiContainer,
    query: Optional[str] = None,
) -> List[QueryResult]:
    """Extract VDJDB data and optionally query for TCRs.

    Source code: https://github.com/spencerseale/search-vdjdb

    Args:
        di_container:
            Dependency injection container.
        query:
            Path to .toml containing optional TCR query.

    Returns:
        Results for each query
    """

    input = SimpleInput(
        log_level="info",
        query=query,
        output=False,
    )

    runner = di_container.runner(
        input=input,
        logger=di_container.logger(),
        parse=False,
    )

    results: list[QueryResult] = runner.run(
        log_level=input.log_level,
        query=input.query,
        output=input.output,
    )

    # transform to array and upload to tiledb cloud
    for result in results:
        result.tiledb_array(upload=True)

    runner.logger.info("Results uploaded to TileDB Cloud.")

    return results


if __name__ == "__main__":
    ################################
    ### Upload a UDF to TileDB Cloud
    ################################
    client = UdfClient()

    upload = ObjectRegistration(
        name="vdjdb_extract",
        executable=extract_vdjdb,
    )

    client.register_udf(upload)
