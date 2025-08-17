import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Optional
from app.commands.base import CommandInterface, CommandParams
from app.models.result import Result

class PlotCommandParams(CommandParams): # Inherits from CommandParams
    plot_type: str = Field(..., description="The type of chart to generate (e.g., 'bar', 'line').")
    target_column: str = Field(..., description="The numerical column to plot on the y-axis.")
    group_by: List[str] = Field(..., description="The categorical column to plot on the x-axis.")

class PlotCommand(CommandInterface):
    name = "plot_data"
    description = "Generates data for a plot or chart. Use this when the user explicitly asks to 'plot', 'chart', 'draw', or 'visualize' data."
    trigger_words = ["plot", "chart", "graph", "draw", "visualize"]
    pydantic_model = PlotCommandParams

    def execute(self, params: PlotCommandParams, df: pd.DataFrame) -> Result:
        # Step 1: Apply filters using the helper from the base class
        df_filtered = self._apply_filters(df, params.filters)

        # Step 2: Resolve column names using the helper from the base class
        target_column = self._resolve_column(params.target_column, df.columns)
        group_by_columns = [self._resolve_column(col, df.columns) for col in params.group_by]
        
        agg_func = 'sum'
        plot_df = df_filtered.groupby(group_by_columns)[target_column].agg(agg_func).reset_index()
        
        labels_col = group_by_columns[0]
        
        chart_data = {
            "labels": plot_df[labels_col].tolist(),
            "datasets": [{
                "label": f"{agg_func.capitalize()} of {target_column} by {labels_col}",
                "data": plot_df[target_column].tolist(),
                "backgroundColor": 'rgba(76, 175, 80, 0.5)',
                "borderColor": 'rgba(76, 175, 80, 1)',
                "borderWidth": 1,
            }]
        }
        
        return Result(
            result_type='plot',
            message="Plot data generated successfully.",
            plot_data={"type": params.plot_type, "data": chart_data}
        )
