"""Dependency injection container for the search_vdjdb package."""

import sys
from logging import Logger, getLogger, StreamHandler, Formatter

from attrs import define 


from search_vdjdb._config import ArgsConfig, ValidatedInput
from search_vdjdb._runner import SearchVdjdbRunner


@define
class DiContainer:
    """Dependency injector."""
    
    namespace: str = "prod"
    
    def logger(self) -> Logger:
        """Init logger"""
        
        logger = getLogger(__name__)
        logger.propagate = False  # don't propagate to root logger
        logger.addHandler(StreamHandler(sys.stdout))

        # init format
        lformat = Formatter(
            fmt="%(asctime)s -- %(message)s\n",
            datefmt="%d-%b-%y %H:%M:%S",
        )
        # set the format for the logger
        logger.handlers[0].setFormatter(lformat)

        return logger
    
    def config(self) -> ArgsConfig:
        
        return ArgsConfig()
    
    def runner(self, input: ValidatedInput, logger: Logger) -> SearchVdjdbRunner:
        
        return SearchVdjdbRunner(
            params=input,
            logger=logger,
            parse=True,
        )