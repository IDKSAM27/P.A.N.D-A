from pandas import DataFrame
from typing import Any, Dict

class DataProcessorInterface():
    @abstractmethod
    def process(self, data: DataFrame, intent: Dict[str, Any]) -> DataFrame:
        pass
