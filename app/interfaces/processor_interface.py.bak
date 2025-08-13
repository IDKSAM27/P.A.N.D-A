from abc import ABC, abstractmethod
import pandas as pd
from app.models.intent import Intent
from app.models.result import Result

class ProcessorInterface(ABC):
    """
    Abstract Base Class for a data processor.
    
    This interface defines the contract for executing a structured Intent
    against a dataset. Any class that performs data operations (e.g., using
    pandas, SQL, etc.) should inherit from this interface and implement
    the execute method.
    """

    @abstractmethod
    def execute(self, intent: Intent, df: pd.DataFrame) -> Result:
        """
        Executes the given intent on the pandas DataFrame.

        Args:
            intent (Intent): The structured command to execute.
            df (pd.DataFrame): The dataframe to operate on.

        Returns:
            Result: An object containing the result of the operation.
        """
        pass
