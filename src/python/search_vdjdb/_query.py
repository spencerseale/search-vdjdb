"""Obtain up-to-date public TCR data from VDJdb containing TCR specificity data.

VDJdb - https://vdjdb.cdr3.net/
"""

import logging
import requests
from urllib.request import urlopen
from typing import Sequence, List, Mapping, Optional
from io import BytesIO
import os
import toml

import pandas as pd
from zipfile import ZipFile

def _extract_dfs(
    zip_url: str,
    files: Sequence[str]
) -> List[pd.DataFrame]:
    """ Extract files as data frames from a compressed file. 

    Args:
        zip_url: path to compressed target.
        files: files to extract from compressed target.

    Returns:
        uncompressed files as dataframe representations.
    """

    zip_resp = urlopen(zip_url)

    all_contents = ZipFile(BytesIO(zip_resp.read()))

    dfs = []

    for selection in files:

        try:

            dfs.append(pd.read_csv(all_contents.open(selection), sep = "\t"))

        except KeyError:

            logging.info("%s was not found, skipping.." % selection)

    return dfs

class PublicTcrDb():
    """ Groups methods relating to fetching tcr records from public tcr dbs.

    Attributes:
        vdjdb_gene: VDJdb colname containing the loci.
        vdjdb_cdr3: VDJdb colname containing the CDR3 sequence.
        vdjdb_v: VDJdb colname containing the V gene
        vdjdb_j: VDJdb colname containing the J gene
        vdjdb_complex: identifier for a single complex, beta and alpha loci
            of the same receptor have the sample complex index.
    """

    def __init__(
        self,
        vdjdb_gene: str = "gene",
        vdjdb_cdr3: str = "cdr3",
        vdjdb_v: str = "v.segm",
        vdjdb_j: str = "j.segm",
        vdjdb_complex: str = "complex.id"
    ) -> None:

        # vdjdb construct column names
        self.vdjdb_gene = vdjdb_gene
        self.vdjdb_cdr3 = vdjdb_cdr3
        self.vdjdb_v = vdjdb_v
        self.vdjdb_j = vdjdb_j
        self.vdjdb_complex = vdjdb_complex
        self.vdjdb = None

    def _fix_vj_format(self) -> None:
        """ For v/j segments listed as TRAV8-1 for example, need to transform to
                TRAV08-01 so that db annotation is in line with Adaptive's formatting 
                (My current company).
        """

        # holds common patterns to match and what to replace if found
        pat_rep = {
            "(T)(R[ABVJ]+)(.*)": r"\1C\2\3",  # handles TRVB to TCRVB
            "(?P<tcr>[TCRABVJ]+)(\d)(?!\d)": r"\g<tcr>0\2",  # using named capture group 'tcr' to avoid capture group \n issues
            "(?P<dash>\-)(\d)(?!\d)": r"\g<dash>0\2"  # handles -4 to -04
        }

        # iteratively look for known patterns to change and fix for v and j
        for p, r in pat_rep.items():
            self.vdjdb[[self.vdjdb_v, self.vdjdb_j]] = self.vdjdb[[self.vdjdb_v, self.vdjdb_j]] \
                .replace(
                    to_replace=p,
                    value=r,
                    regex=True,
                )

    def get_vdjdb(
        self,
        api: str = "https://api.github.com",
        latest_release: str = "repos/antigenomics/vdjdb-db/releases/latest",
        txt_file: str = "vdjdb.slim.txt",
        cache: bool = True
    ) -> None:
        """Obtain a copy of VDJdb from the latest available release.

        Args:
            api: github api.
            latest_release: endpoint to latest release.
            txt_file: db file to extract from compression.
            cache: whether to cache VDJdb locally for faster retrieval later.
        """

        resp = requests.get(os.path.join(api, latest_release))
        resp.raise_for_status()
        
        zip_uri = resp.json()["assets"][0]["browser_download_url"]
        
        print(zip_uri)

        try:
            self.vdjdb = _extract_dfs(
                zip_url = zip_uri,
                files = [txt_file]
            )[0]

            self._fix_vj_format()

            if cache:  # archive a local to reduce scraping bandwidth 
                # can be quite large so compress it
                self.vdjdb.to_csv(
                    ".vdjdb_tsv.gz",
                    sep = "\t",
                    index = False,
                    compression = "gzip"
                )

                logging.info("VDJdb cached to local as .vdjdb_tsv.gz")

        except IndexError:
            logging.error("Could not locate %s in VDJdb release" % txt_file)

    def find(
        self,
        vdjdb_search: Optional[Mapping[str, str]] = None,
        construct_only: bool = True,
    ) -> pd.DataFrame:
        """ Query attached DBs for matches.

        Args:
            vdjdb_search: parameters to filter db by.
            construct_only: whether to return only annotations pertinent to the TCR
                construct (cdr3, v, j).
        
        Returns:
            Filtered dataframe based on query params.
        """

        if vdjdb_search:
            # get vdjdb if not previously done
            if self.vdjdb is None:
                try:
                    self.vdjdb = pd.read_csv(
                        ".vdjdb_tsv.gz",
                        sep = "\t"
                    )

                except FileNotFoundError:
                    self.get_vdjdb()

            # dynamically string together filtering operations
            v_row_filt = [
                f"`{k}`.str.contains('{v}', regex = False)" for k, v in vdjdb_search.items()
            ]

            v_result = self.vdjdb.query(" & ".join(v_row_filt), engine = "python")

            if construct_only:
                # select only cols relating to construct,
                # these cols are specified in attributes
                v_result = v_result.loc[
                    :,
                    [self.__dict__[a] for a in self.__dict__ if a.startswith("vdjdb_")]
                ]

            # complex identifies same alpha-beta pair; also list alpha before beta
            return v_result.sort_values([self.vdjdb_complex, self.vdjdb_gene])

        else:
            logging.warning("No query params specified, returning entire VDJdb.")

            return self.vdjdb
        
    @classmethod
    def file_query(cls, query: str, output: bool = False) -> None:
        
        cdir, cpath = query.rsplit("/", 1)
        print(cdir)
        print(cpath)
        # queries = toml.loads(files(cdir.replace("/", ".")).joinpath(cpath).read_text())
        # queries = toml.
        
        # load toml file from str path 
        queries = toml.load(query)
        print(queries)
        
        
        vdjdb_constr = cls()
        vdjdb = vdjdb_constr.get_vdjdb()
        
        print()
        print(vdjdb_constr.vdjdb)
        
        # for id in queries:
        
            # logging.info("Filtering VDJdb results for: %s" % "".join([f"\n\t>>> {k}: {v}" for k, v in query.items()]))
            
        #     print(id)
            
            # id_result = vdjdb_constr.find(vdjdb_search = queries[id], construct_only = False)
            
        #     print(id_result)
        
            # if output:
            #     outpath = os.path.join("vdjdb_queries", f"{id}.tsv")
            #     os.makedirs(os.path.dirname(outpath), exist_ok = True)

            #     # for this usage example out will contain a single index
            #     id_result.to_csv(
            #         outpath,
            #         sep = "\t",
            #     )