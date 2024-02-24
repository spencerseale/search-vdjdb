"""Obtain up-to-date public TCR-specificity data from Public TCR DBs.

Currently available:
    * VDJdb (https://vdjdb.cdr3.net)
"""

from logging import Logger, getLogger
import requests
from urllib.request import urlopen
from typing import Sequence, List, Mapping, Optional
from io import BytesIO
import os
import toml

from dataclasses import dataclass
from attrs import define, field
from pydantic.dataclasses import dataclass as pydantic_dataclass
import pandas as pd
from zipfile import ZipFile
import tiledb
import tiledb.cloud


@dataclass(frozen=False)
class QueryResult:
    """Results of a query."""

    id: str
    """Identifier for the query."""
    result: pd.DataFrame
    """Results of a query."""
    query: Mapping[str, str]
    """Query parameters used to obtain results."""
    db: str
    """Database queried."""
    path: str = field(init=False)

    def output(self, path: str) -> None:
        """Output results to a file.

        Args:
            path:
                Path to output file.

        Returns:
            Path to output file.
        """

        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.result.to_csv(path, sep="\t")

        self.path = path

    def tiledb_array(
        self,
        upload: bool = False,
        tiledb_user: str = "spencerseale17",
        s3_bucket: str = "spencerseale",
    ) -> None:
        """Upload results to Tiledb Cloud.

        D3 and Tiledb user and bucket are hardcoded for now
        but ought to be encoded as environment variables.

        Args:
            upload:
                Whether to upload to TileDB Cloud.
            tiledb_user:
                TileDB Cloud user.
            s3_bucket:
                S3 bucket to upload to.
        """

        config = tiledb.Config()
        config["rest.token"] = os.environ["TILEDB_TOKEN"]

        if upload:
            uri = f"tiledb://{tiledb_user}/s3://{s3_bucket}/{self.id}"
        else:
            uri = self.id + "_TileDBarray"

        tiledb.from_pandas(uri, self.result, ctx=tiledb.Ctx(config))


@pydantic_dataclass(frozen=True)
class VdjdbMeta:
    """VDJdb metadata for parsing."""

    gene: str = "gene"
    """VDJdb colname containing the loci."""
    cdr3: str = "cdr3"
    """VDJdb colname containing the CDR3 sequence."""
    v: str = "v.segm"
    """VDJdb colname containing the V gene"""
    j: str = "j.segm"
    """VDJdb colname containing the J gene"""
    complex: str = "complex.id"
    """Identifier for a single complex, beta and alpha loci of the
    same receptor have the sample complex index."""


@define
class PublicTcrDb:
    """Groups methods relating to fetching tcr records from public tcr dbs."""

    vdjdb_meta: VdjdbMeta = field(factory=VdjdbMeta)
    logger: Optional[Logger] = field()

    @logger.default
    def _logger(self) -> Logger:
        return getLogger(__name__)

    vdjdb: pd.DataFrame = field(init=False)

    def _fix_vj_format(self) -> None:
        """For v/j segments listed as TRAV8-1 for example, need to transform to
        TRAV08-01 so that db annotation is in line with Adaptive's formatting
        (My current company).

        Uses named capture group 'tcr' to avoid capture group \n issues.
        """

        # holds common patterns to match and what to replace if found
        pat_rep = {
            "(T)(R[ABVJ]+)(.*)": r"\1C\2\3",  # handles TRVB to TCRVB
            "(?P<tcr>[TCRABVJ]+)(\d)(?!\d)": r"\g<tcr>0\2",
            "(?P<dash>\-)(\d)(?!\d)": r"\g<dash>0\2",  # handles -4 to -04
        }

        # iteratively look for known patterns to change and fix for v and j
        for p, r in pat_rep.items():
            self.vdjdb[[self.vdjdb_meta.v, self.vdjdb_meta.j]] = self.vdjdb[
                [self.vdjdb_meta.v, self.vdjdb_meta.j]
            ].replace(
                to_replace=p,
                value=r,
                regex=True,
            )

    def _extract_dfs(
        self,
        zip_url: str,
        files: Sequence[str],
        human_only: bool = True,
    ) -> List[pd.DataFrame]:
        """Extract files as data frames from a compressed file.

        Args:
            zip_url:
                Path to compressed target.
            files:
                Files to extract from compressed target.
            human_only:
                Whether to filter for human records only.

        Returns:
            uncompressed files as dataframe representations.
        """

        zip_resp = urlopen(zip_url)

        all_contents = ZipFile(BytesIO(zip_resp.read()))

        dfs = []
        for selection in files:
            try:
                dbdf = pd.read_csv(
                    all_contents.open(selection),
                    sep="\t",
                    dtype=str,
                )

                # perform some fitlering for tiledb upload
                dbdf = dbdf.fillna("")
                # add column with today's date for tracking
                dbdf["date_pulled"] = pd.to_datetime("today").strftime("%Y-%m-%d")
                dbdf["date_pulled"] = dbdf["date_pulled"].astype("datetime64[ns]")

                if human_only:
                    dbdf = dbdf[dbdf["species"] == "HomoSapiens"].reset_index(drop=True)

                dfs.append(dbdf)

            except KeyError:
                self.logger.debug("%s was not found, skipping.." % selection)

        return dfs

    def get_vdjdb(
        self,
        api: str = "https://api.github.com",
        latest_release: str = "repos/antigenomics/vdjdb-db/releases/latest",
        txt_file: str = "vdjdb.slim.txt",
        cache: bool = True,
    ) -> None:
        """Obtain a copy of VDJdb from the latest available release.

        Args:
            api:
                Github api.
            latest_release:
                Edpoint to latest release.
            txt_file:
                DB file to extract from compression.
            cache:
                Whether to cache VDJdb locally for faster retrieval later.
        """

        resp = requests.get(os.path.join(api, latest_release))
        resp.raise_for_status()

        zip_uri = resp.json()["assets"][0]["browser_download_url"]

        self.logger.info("VDJdb release found at %s" % zip_uri)

        try:
            self.vdjdb = self._extract_dfs(zip_url=zip_uri, files=[txt_file])[0]

            self._fix_vj_format()

            if cache:  # archive a local to reduce scraping bandwidth
                # can be quite large so compress it
                self.vdjdb.to_csv(
                    ".vdjdb_tsv.gz",
                    sep="\t",
                    index=False,
                    compression="gzip",
                )

                self.logger.info("VDJdb cached to local as .vdjdb_tsv.gz")

        except IndexError:
            self.logger.error("Could not locate %s in VDJdb release" % txt_file)

    def find(
        self,
        vdjdb_search: Optional[Mapping[str, str]] = None,
        construct_only: bool = True,
    ) -> pd.DataFrame:
        """Query attached DBs for matches.

        Args:
            vdjdb_search:
                Parameters to filter db by.
            construct_only:
                Whether to return only annotations pertinent to the TCR
                construct (cdr3, v, j).

        Returns:
            Filtered dataframe based on query params.
        """

        if vdjdb_search:
            # get vdjdb if not previously done
            if self.vdjdb is None:
                try:
                    self.vdjdb = pd.read_csv(".vdjdb_tsv.gz", sep="\t")

                except FileNotFoundError:
                    self.get_vdjdb()

            # dynamically string together filtering operations
            v_row_filt = [
                f"`{k}`.str.contains('{v}', regex = False)"
                for k, v in vdjdb_search.items()
            ]

            v_result = self.vdjdb.query(" & ".join(v_row_filt), engine="python")

            if construct_only:
                # select only cols relating to construct,
                # these cols are specified in attributes
                v_result = v_result.loc[
                    :,
                    [self.__dict__[a] for a in self.__dict__ if a.startswith("vdjdb_")],
                ]

            # complex identifies same alpha-beta pair; also list alpha before beta
            return v_result.sort_values([self.vdjdb_meta.complex, self.vdjdb_meta.gene])

        else:
            self.logger.warning("No query params specified, returning entire VDJdb.")

            return self.vdjdb

    @classmethod
    def file_query(
        cls,
        query: str,
        output: bool = False,
        logger: Optional[Logger] = None,
    ) -> List[QueryResult]:
        """Query public TCR DB from a file listing queries.

        Args:
            query:
                Path to .toml containing queries.
            output:
                Whether to output results to file.
            logger:
                Logger instance.

        Returns:
            Results for each query.
        """

        tcrdb = cls(logger=logger)
        tcrdb.get_vdjdb()

        # load toml file from str path
        if query:
            queries = toml.load(query)

            tcrdb.logger.info(
                "Filtering VDJdb results for: %s"
                % "".join([f"\n\t>>> {k}: {v}" for k, v in queries.items()])
            )

            all_results = []
            for id in queries:
                id_result = tcrdb.find(vdjdb_search=queries[id], construct_only=False)

                qresult = QueryResult(
                    id=id,
                    result=id_result,
                    query=queries[id],
                    db="vdjdb",  # harcoded until more dbs are added
                )

                if output:
                    qresult.output(path=os.path.join(".vdjdb_queries", f"{id}.tsv"))

                all_results.append(qresult)

            return all_results

        else:
            tcrdb.logger.info("No query file specified, returning entire VDJdb.")
            qresult = QueryResult(
                id="full_vdjdb", result=tcrdb.vdjdb, query={}, db="vdjdb"
            )

            if output:
                qresult.output(path=os.path.join(".vdjdb_queries", "vdjdb_full.tsv"))

            return [qresult]
