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

    def execute(self, intent: Intent, df: pd.DataFrame) -> Result:
        try:
            actual_columns = df.columns.tolist()

            # --- FIX: Resolve column names before using them ---
            def get_resolved_column(name):
                resolved = self._find_closest_column_name(name, actual_columns)
                if not resolved:
                    raise KeyError(f"Column '{name}' could not be found in the dataset.")
                return resolved

            # Resolve target column
            target_column = get_resolved_column(intent.target_column) if intent.target_column else None
            
            # Resolve group_by columns
            group_by_columns = [get_resolved_column(col) for col in intent.group_by] if intent.group_by else []

            # Resolve filter columns
            resolved_filters = {}
            if intent.filters:
                for col, val in intent.filters.items():
                    resolved_col = get_resolved_column(col)
                    resolved_filters[resolved_col] = val
            
            df_filtered = self._apply_filters(df, resolved_filters)
            
            # ... (The rest of the logic uses the resolved names) ...

            if intent.operation == 'count' and not group_by_columns:
                count = len(df_filtered)
                return Result(result_type='value', data=count, message=f"{intent.description} Result: {count}.")

            if group_by_columns:
                if intent.operation == 'count':
                    result_data = df_filtered.groupby(group_by_columns).size()
                    message = f"Successfully performed count grouped by {group_by_columns}."
                else:
                    if not target_column:
                         raise ValueError("A target column is required for this grouped aggregation.")
                    result_data = df_filtered.groupby(group_by_columns)[target_column].agg(intent.operation)
                    message = f"Successfully performed '{intent.operation}' on '{target_column}' grouped by {group_by_columns}."
                
                return Result(result_type='table', data=result_data.reset_index(name='result').to_dict(orient='records'), message=message)
            
            if target_column:
                result_val = df_filtered[target_column].agg(intent.operation)
                return Result(result_type='value', data=result_val, message=f"The result of '{intent.operation}' on '{target_column}' is {result_val}.")

            return Result(result_type='error', message=f"Could not determine the correct action for the intent: {intent.description}")

        except (KeyError, ValueError) as e:
            return Result(result_type='error', message=str(e))
        except Exception as e:
            return Result(result_type='error', message=f"An unexpected error occurred: {e}")

    def _apply_filters(self, df: pd.DataFrame, filters: dict) -> pd.DataFrame:
        if not filters:
            return df
        
        df_filtered = df.copy()
        for column, value in filters.items():
            df_filtered = df_filtered[df_filtered[column].astype(str).str.lower() == str(value).lower()]
        
        return df_filtered
