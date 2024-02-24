"""Top-level runner for search-vdjdb."""

from logging import Logger

from click import Command, Option
from attrs import define, field

from search_vdjdb._query import PublicTcrDb, QueryResult
from search_vdjdb._config import ValidatedInput


@define
class SearchVdjdbRunner:
    """Runner for search-vdjdb."""

    params: ValidatedInput
    """Validated input parameters."""
    logger: Logger
    """Logger instance."""
    parse: bool = True
    """Parse the command line arguments."""
    _command: Command = field(init=False)
    """Click-formed command to run."""

    def __attrs_post_init__(self) -> None:
        if self.parse:
            self._parse()

    def _parse(self) -> None:
        """Parse the command line arguments to form the command.

        A dataclass holds all the params to encode individual Option instances.
        """

        click_params = [Option(**opt) for opt in self.params]

        self._command = Command(
            name="search-vdjdb", params=click_params, callback=self.run
        )

    def __call__(self) -> None:
        """Call the command."""

        if self._command:
            return self._command()

        else:
            raise ValueError("Runer not initialized.")

    def run(
        self,
        log_level: str,
        query: str,
        output: bool,
    ) -> list[QueryResult]:
        """Run the tcrgb-vn-agg workflow."""

        self.logger.setLevel(log_level.upper())
        self.logger.debug("Logger initialized at level: %s", log_level.upper())

        self.logger.info("Initiating the search-vdjdb entrypoint.")

        self.logger.info(
            "Parsed arguments: \n\t-- %s"
            % "\n\t-- ".join(f"{k}: {v}" for k, v in locals().items() if k != "self")
        )

        results = PublicTcrDb.file_query(query=query, output=output, logger=self.logger)

        self.logger.info("Searching complete.")

        return results
