from typing import Any, Optional
from pydantic import BaseModel

class Result(BaseModel):
    """
    Represents the output of a data processing operation.
    
    This model standardizes the data structure returned after an intent
    is executed, making it easy for other parts of the system (like a UI)
    to handle different types of outcomes.
    """
    result_type: str = "message"  # e.g., 'table', 'plot', 'value', 'error'
    data: Optional[Any] = None
    message: str

    class Config:
        # Allows creating the model from a dictionary or other attributes
        from_attributes = True
