from abc import ABC, abstractmethod
import pandas as pd
from pydantic import BaseModel
from app.models.result import Result
from typing import List, Optional, Dict, Any

class CommandParams(BaseModel):
    """A base model for command parameters, now including filters."""
    filters: Optional[Dict[str, Any]] = None

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

    def _resolve_column(self, name: str, df_columns: List[str]) -> str:
        """Finds the actual column name that best matches the target name."""
        def normalize(s: str) -> str:
            # Converts to lowercase and removes spaces and underscores
            return s.lower().replace("_", "").replace(" ", "")

        if not name:
            raise ValueError("Column name cannot be empty.")
        
        normalized_name = normalize(name)
        for col in df_columns:
            if normalize(col) == normalized_name:
                return col
        
        raise KeyError(f"Column not found: {name}")

    def _apply_filters(self, df: pd.DataFrame, filters: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """Applies filters to the dataframe, resolving column names."""
        if not filters:
            return df
        
        df_filtered = df.copy()
        for column, value in filters.items():
            resolved_col = self._resolve_column(column, df.columns.tolist())
            # Convert both to string and lower for case-insensitive comparison
            df_filtered = df_filtered[df_filtered[resolved_col].astype(str).str.lower() == str(value).lower()]
        
        return df_filtered
