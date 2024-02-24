# search-vdjdb


### Background 

This simple python tool serves to obtain up-to-date public T-cell receptor (TCR) data from VDJdb - a popular database containing TCR specificity data.

VDJdb - https://vdjdb.cdr3.net/

Data is aggregated from peer-reviewed publications and absorbed in non-routine intervals by administrators. Due to these sporadic updates, ensuring an up-to-date version of VDJdb is queried as part of this workflow is critical to ensuring a complete database is available to users. For example during the COVID-19 pandemic, TCR specificity data for viral epitopes was added giving vaccine developers information on COVID-19 epitopes to target. Querying a dated database would miss these valuable additions.

The heterodimer T-cell receptors (beta and alpha subunits) encode specificity for any possible antigen that they may encounter. This specificity is encoded via a process known as "VDJ recombination" (in alpha the D gene is absent and thus VJ recombination) where 3 gene segments, V, D, and J, randomly shuffle. This randomness results in a variety of receptors capable of arming the adaptive immune system against any type of pathogen. At the center of this binding domain exists an additional region, the Complimentary Determining Region 3 (CDR3), which makes direct contact with an antigen. Together, these motifs define the variable region of a receptor and are commonly used as a proxy for the make-up of an entire receptor, and thus T-cell. 

Querying this database provides valuable insight into annotation information reported in the literature. 

### Installation

This package relies on poetry for seamless dependency management.

* https://python-poetry.org/docs/#:~:text=a%20supported%20one.-,Installation,-Poetry%20provides%20a

* Ensure your python3 runtime matches that specified in `pyproject.toml`. This can be done with conda or pyenv and ensure that runtime is activated.

* From the project root, install: `poetry install`

### Basic Usage

* Run some example cases through the tool to demonstrate it's usage: `poetry run python -m search_vdjdb.entry -q src/python/search_vdjdb/configs/query_examples.toml`. 

* The example queries are contained in `search_vdjdb.configs.query_examples.toml`, you can edit this file to include additional values to filter for as key, value pairs. 

* Save queries as individual files by passing `--output` along with execution.

* For more control, import search_vdjdb.query_db into your workflow and instantiate a `query_db.PublicTcrDb` object to programatically gain access to the latest VDJdb release.

### Additional Considerations

* Calling `PublicTcrDb.get_vdjdb()` defaults to caching a local gzipped VDJdb. Subsequent method calls and queries will overwrite this file. However, calling into `PublicTcrDb.find()` will first look for a cached VDJdb prior to scraping a new copy. If you wish to update your local VDJdb in between query commands, either remove the local file from your system or execute `PublicTcrDb.get_vdjdb()` again to refresh your copy.
