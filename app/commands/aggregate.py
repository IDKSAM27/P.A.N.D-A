import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Optional
from app.commands.base import CommandInterface
from app.models.result import Result

class AggregateCommandParams(BaseModel):
    agg_func: str = Field(..., description="The aggregation function to use (e.g., 'sum', 'mean', 'count').")
    target_column: Optional[str] = Field(None, description="The column to perform the aggregation on.")
    group_by: Optional[List[str]] = Field(None, description="A list of columns to group the data by.")
    limit: Optional[int] = Field(None, description="The number of rows to return (for top/lowest queries).")
    sort_order: str = Field('desc', description="'asc' for ascending (lowest) or 'desc' for descending (highest).")

class AggregateCommand(CommandInterface):
    name = "aggregate_data"
    description = "Performs aggregation functions like sum, mean, count, etc., on a column, optionally grouped by other columns. This is used for all 'top N' or 'lowest N' ranking queries."
    trigger_words = ["total", "sum", "average", "mean", "count", "top", "lowest", "highest", "bottom"]
    pydantic_model = AggregateCommandParams

    def execute(self, params: AggregateCommandParams, df: pd.DataFrame) -> Result:
        if not params.target_column and params.agg_func != 'count':
            raise ValueError(f"A target column is required for the '{params.agg_func}' operation.")

        if params.group_by:
            if params.agg_func == 'count':
                agg_result = df.groupby(params.group_by).size()
            else:
                agg_result = df.groupby(params.group_by)[params.target_column].agg(params.agg_func)
            
            result_df = agg_result.reset_index(name='result')
            ascending = params.sort_order == 'asc'
            result_df = result_df.sort_values(by='result', ascending=ascending)

            if params.limit:
                result_df = result_df.head(params.limit)
            
            return Result(result_type='table', data=result_df.to_dict(orient='records'), message="Aggregation successful.")
        
        else:
            result_val = df[params.target_column].agg(params.agg_func)
            return Result(result_type='value', data=result_val, message="Aggregation successful.")
