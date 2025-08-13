from abc import ABC, abstractmethod
import pandas as pd
from pydantic import BaseModel
from app.models.result import Result # We will keep the Result model

class CommandParams(BaseModel):
    """A base model for command parameters."""
    pass

class CommandInterface(ABC):
    """The abstract base class for all command modules."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the command."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A short description of what the command does."""
        pass
    
    @property
    @abstractmethod
    def trigger_words(self) -> list[str]:
        """Keywords that suggest this command should be used."""
        pass

    @property
    @abstractmethod
    def pydantic_model(self) -> type[BaseModel]:
        """The Pydantic model for this command's specific parameters."""
        pass

    @abstractmethod
    def execute(self, params: BaseModel, df: pd.DataFrame) -> Result:
        """The method to execute the command's logic."""
        pass
