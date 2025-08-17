import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Optional
from app.commands.base import CommandInterface, CommandParams
from app.models.result import Result

class AggregateCommandParams(CommandParams): # Inherits from CommandParams to get 'filters'
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
        # Step 1: Apply filters using the helper from the base class
        df_filtered = self._apply_filters(df, params.filters)

        # Step 2: Resolve column names using the helper from the base class
        target_column = self._resolve_column(params.target_column, df.columns) if params.target_column else None
        group_by_columns = [self._resolve_column(col, df.columns) for col in params.group_by] if params.group_by else []

        if not target_column and params.agg_func not in ['count']:
            raise ValueError(f"A target column is required for the '{params.agg_func}' operation.")

        if group_by_columns:
            if params.agg_func == 'count':
                agg_result = df_filtered.groupby(group_by_columns).size()
            else:
                agg_result = df_filtered.groupby(group_by_columns)[target_column].agg(params.agg_func)
            
            result_df = agg_result.reset_index(name='result')
            ascending = params.sort_order == 'asc'
            result_df = result_df.sort_values(by='result', ascending=ascending)

            if params.limit:
                result_df = result_df.head(params.limit)
            
            return Result(result_type='table', data=result_df.to_dict(orient='records'), message="Aggregation successful.")
        
        else:
            result_val = df_filtered[target_column].agg(params.agg_func)
            return Result(result_type='value', data=result_val, message="Aggregation successful.")
