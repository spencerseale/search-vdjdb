"""Example of how to execute compute in TileDB Cloud or locally."""

from search_vdjdb.di_container import DiContainer
from search_vdjdb.tiledb.client import UdfClient, UdfInput
from search_vdjdb.tiledb.registrations import extract_vdjdb

if __name__ == "__main__":
    di = DiContainer()

    #################################
    ### Execute a UDF in TileDB Cloud
    #################################
    client = UdfClient()
    input = UdfInput(name="test", udf=extract_vdjdb, args=[di])

    # DOESN'T WORK, can't customize Docker image used in running UDF
    # client.run_udf(input)

    #########################
    ### Execute a UDF locally
    #########################
    out = extract_vdjdb(di)
