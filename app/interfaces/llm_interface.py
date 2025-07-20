from abc import ABC, abstractmethod
from typing import List
from app.models.intent import Intent

class LLMInterface(ABC):
    """
    Abstract Base Class for a Large Language Model parser. 

    This interface defines the contrast for any class that aims to parse
    a natural language command into a structured Intent object.
    """

    @abstractmethod
    def parse_command(self, command: str, df_columns: List[str]) -> Intent:
        """
        Parses a natural language command to extract a structured intent.

        Args:
            command(str): The natural language command from the user.
            df_columns (List[str]): A list of column names from the dataframe
            to provide context to the LLM.

        Returns:
            Intent: A structured Intent object representing the user's request.
        """

        pass