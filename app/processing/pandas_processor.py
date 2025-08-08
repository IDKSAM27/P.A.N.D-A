import pandas as pd
from typing import List, Optional
from app.interfaces.processor_interface import ProcessorInterface
from app.models.intent import Intent
from app.models.result import Result

class PandasProcessor(ProcessorInterface):
    """
    A data processor that uses pandas and is resilient to minor column name variations.
    """
    def _normalize_name(self, name: str) -> str:
        """Helper to standardize column names for comparison."""
        return name.lower().replace("_", "").replace(" ", "")

    def _find_closest_column_name(self, target_name: str, actual_columns: List[str]) -> Optional[str]:
        """Finds the actual column name that best matches the target name."""
        normalized_target = self._normalize_name(target_name)
        for col in actual_columns:
            if self._normalize_name(col) == normalized_target:
                return col
        return None

    # voice_data_assistant/app/processing/pandas_processor.py
# (No changes to imports or the first part of the class)
# Replace the 'execute' method with this new version:

    def execute(self, intent: Intent, df: pd.DataFrame) -> Result:
        try:
            actual_columns = df.columns.tolist()

            def get_resolved_column(name):
                resolved = self._find_closest_column_name(name, actual_columns)
                if not resolved:
                    raise KeyError(f"Column '{name}' could not be found in the dataset.")
                return resolved

            target_column = get_resolved_column(intent.target_column) if intent.target_column else None
            group_by_columns = [get_resolved_column(col) for col in intent.group_by] if intent.group_by else []

            resolved_filters = {}
            if intent.filters:
                for col, val in intent.filters.items():
                    resolved_col = get_resolved_column(col)
                    resolved_filters[resolved_col] = val
            
            df_filtered = self._apply_filters(df, resolved_filters)

            # --- NEW: Plotting Logic ---
            if intent.operation == 'plot':
                if not group_by_columns or not target_column:
                    raise ValueError("Plotting requires at least one grouping column and a target column.")

                # For plotting, we always perform a 'sum' aggregation for simplicity
                agg_func = 'sum'
                plot_df = df_filtered.groupby(group_by_columns)[target_column].agg(agg_func).reset_index()
                
                # The first group_by column will be our labels (x-axis)
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
                    message=intent.description,
                    plot_data={
                        "type": intent.plot_type or 'bar',
                        "data": chart_data
                    }
                )

            # --- Existing Logic ---
            if intent.operation == 'count' and not group_by_columns:
                # ... (no change here)
            
            if group_by_columns:
                # ... (no change here)
            
            if target_column:
                # ... (no change here)

            return Result(result_type='error', message=f"Could not determine action for: {intent.description}")

        except (KeyError, ValueError) as e:
            return Result(result_type='error', message=str(e))
        except Exception as e:
            return Result(result_type='error', message=f"An unexpected error occurred: {e}")

