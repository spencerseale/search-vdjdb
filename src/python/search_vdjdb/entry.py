

from logging import Logger
from attrs import define, field

from search_vdjdb.di_container import DiContainer

@define
class SearchVdjdbEntrypoint:
    """Entrypoint for search_vdjdb package."""
    
    
    di: DiContainer = field()
    """Dependency injection container."""
    @di.default
    def _di_default(self) -> DiContainer:
        return DiContainer()
    logger: Logger = field()
    @logger.default
    def _logger_default(self) -> Logger:
        return self.di.logger()
    
    @logger.validator
    def _logger_validator(self, attribute, value) -> None:
        if not isinstance(value, Logger):
            raise ValueError(f"Expected Logger, got {type(value)}")
    
    def run(self) -> None:
        config = self.di.config()
        runner = self.di.runner(input=config.load(), logger=self.logger)
        
        # print()
        # print(runner.params)
        # print(runner.params.log_level.upper())
        # self.logger.info(
        #     "Parsed arguments: \n\t-- %s"
        #     % "\n\t-- ".join(f"{k}: {v}" for k, v in vars(runner.params).items())
        # )

        
        
        runner()
        # runner.run(config)
        
        
if __name__ == "__main__":
    
    entry = SearchVdjdbEntrypoint()
    
    entry.run()