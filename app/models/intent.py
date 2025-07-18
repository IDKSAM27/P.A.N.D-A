from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class Intent(BaseModel):
    # Represents the structured user intent extracted from a natural language command. 
    operation: str = Field(..., description="The primary data operation to perform, e.g., 'mean', 'sum', 'count', 'plot'.")
    target_column: Optional[str] = Field(None, description="The main column the operation applies to, e.g., 'sales'.")
    group_by: Optional[List[str]] = Field(None, description="A list of columns to group the data by, e.g., ['region', 'product'].")
    filters: Optional[str] = Field(None, description="A dictionary of filters to apply, e.g., {'year': '2025'}.")
    description: Optional[str] = Field(None, description="A natural language description of the operation to be performed.")

    class Config:
        # Allows creating the model from a dictionary
        from_attributes = True 
