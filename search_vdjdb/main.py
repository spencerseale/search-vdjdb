""" Top-level runner for search-vdjdb. 

Runs example code to demo usage.
"""

from typing import Mapping, Optional
import argparse
import logging
from importlib_resources import files
import os

import toml
import pandas as pd

import search_vdjdb.query_db as query_db

def main(
    query: Mapping[str, str],
    query_id: str, 
    ptb: Optional[query_db.PublicTcrDb] = None,
    output: bool = False
) -> None:
    """ Runner to demonstrate utility of query_db.

    The output is logged and written to specified dir.

    Args:
        query: params to filter VDJdb by.
        query_id: id for query as specified in config.
        ptb: db object.
        output: whether to save query results to $PWD.
    """

    logging.info("Filtering VDJdb results for: %s" % "".join([f"\n\t>>> {k}: {v}" for k, v in query.items()]))

    ptb = ptb or query_db.PublicTcrDb()

    out = ptb.find(vdjdb_search = query, construct_only = False)

    # empty list if not results for query
    if out.empty:

        logging.info("No hits found for %s." % query_id)

        # end logic, don't need to check to write out
        return None

    else:

        logging.info("%d results found for %s:\n\n%s" % (len(out.index), query_id, out))

    if output:

        outpath = os.path.join("vdjdb_queries", f"{query_id}.tsv")

        os.makedirs(os.path.dirname(outpath), exist_ok = True)

        # for this usage example out will contain a single index
        out.to_csv(
            outpath,
            sep = "\t",
        )


if __name__ == "__main__":

    pd.set_option("display.max_columns", None)

    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s -- %(message)s\n",
        datefmt = "%d-%b-%y %H:%M:%S"
    )

    parser = argparse.ArgumentParser(
        description = "Form full length TCR constructs from public databases."
    )

    parser.add_argument(
        "-c",
        "--config",
        default = "search_vdjdb.configs",
        help = "Config dir (module path) containing config params."
    )

    parser.add_argument(
        "-e",
        "--examples",
        action = "store_true",
        default = False,
        help = "Run examples to demonstrate library utility."
    )

    parser.add_argument(
        "-o",
        "--output",
        action = "store_true",
        default = False,
        help = "Output query results."
    )

    args = parser.parse_args()

    if args.examples:

        # form once to reuse same VDJdb for repeat queries
        ptb = query_db.PublicTcrDb()

        ptb.get_vdjdb()

        example_queries = toml.loads(
            files(args.config).joinpath("query_examples.toml").read_text()
        )

        for ex in example_queries:

            main(
                query = example_queries[ex], 
                query_id = ex,
                ptb = ptb,
                output = args.output
            )

    else:

        logging.info("Did you mean to run with example usage? Include -e flag.")



