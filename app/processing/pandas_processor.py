import pandas as pd
from app.interfaces.processor_interface import ProcessorInterface
from app.models.intent import Intent
from app.models.result import Result

class PandasProcessor(ProcessorInterface):
    """
    A data processor that uses the pandas library to execute intents.
    """
    def execute(self, intent: Intent, df: pd.DataFrame) -> Result:
        """
        Executes the given intent on the pandas DataFrame.

        Args:
            intent (Intent): The structured command to execute.
            df (pd.DataFrame): The dataframe to operate on.

        Returns:
            Result: An object containing the result of the operation.
        """
        try:
            # --- 1. Apply Filters ---
            # Create a filtered copy of the DataFrame to work with.
            df_filtered = self._apply_filters(df, intent.filters)

            # --- 2. Handle Non-Aggregating Operations ---
            if intent.operation == 'plot':
                # We won't implement the plotting logic here, just acknowledge the intent.
                # The UI layer will handle the actual visualization.
                return Result(
                    result_type='plot',
                    data={'intent': intent.model_dump()}, # Pass intent data to UI for plotting
                    message=f"A plot was requested. Description: {intent.description}"
                )

            # Handle a simple count on the filtered data (no grouping, no target column)
            if intent.operation == 'count' and not intent.group_by and not intent.target_column:
                count = len(df_filtered)
                return Result(
                    result_type='value',
                    data=count,
                    message=f"{intent.description} Result: {count}."
                )

            # --- 3. Handle Grouping and Aggregation ---
            if intent.group_by:
                # Ensure group_by columns are valid
                for col in intent.group_by:
                    if col not in df_filtered.columns:
                        raise KeyError(f"Grouping column '{col}' not found in the dataset.")

                # For 'count', a target column isn't necessary.
                if intent.operation == 'count':
                    result_data = df_filtered.groupby(intent.group_by).size()
                    message = f"Successfully performed count grouped by {intent.group_by}."
                else:
                    # For other aggregations, a target column is required.
                    if not intent.target_column:
                         raise ValueError("A target column is required for this grouped aggregation.")
                    if intent.target_column not in df_filtered.columns:
                        raise KeyError(f"Target column '{intent.target_column}' not found.")
                    
                    result_data = df_filtered.groupby(intent.group_by)[intent.target_column].agg(intent.operation)
                    message = f"Successfully performed '{intent.operation}' on '{intent.target_column}' grouped by {intent.group_by}."

                # Convert the result (which is a pandas Series) to a dictionary for easy use.
                return Result(
                    result_type='table',
                    data=result_data.reset_index(name='result').to_dict(orient='records'),
                    message=message
                )
            
            # --- 4. Handle Simple Aggregation (No Grouping) ---
            if intent.target_column:
                if intent.target_column not in df_filtered.columns:
                    raise KeyError(f"Target column '{intent.target_column}' not found.")
                
                result_val = df_filtered[intent.target_column].agg(intent.operation)
                return Result(
                    result_type='value',
                    data=result_val,
                    message=f"The result of '{intent.operation}' on '{intent.target_column}' is {result_val}."
                )

            # --- 5. Fallback for unhandled cases ---
            return Result(
                result_type='error',
                message=f"Could not determine the correct action for the intent: {intent.description}"
            )

        except (KeyError, AttributeError) as e:
            return Result(result_type='error', message=f"Invalid column name provided: {e}")
        except ValueError as e:
            return Result(result_type='error', message=str(e))
        except Exception as e:
            # Catch any other unexpected pandas/python errors.
            return Result(result_type='error', message=f"An unexpected error occurred during processing: {e}")

    def _apply_filters(self, df: pd.DataFrame, filters: dict) -> pd.DataFrame:
        if not filters:
            return df
        
        df_filtered = df.copy()
        for column, value in filters.items():
            if column not in df_filtered.columns:
                raise KeyError(f"Filter column '{column}' not found in the dataset.")
            
            # This is a simple equality filter. More complex logic (e.g., >, <, contains) could be added here.
            # Using .astype(str) for safer comparison if types are mixed.
            df_filtered = df_filtered[df_filtered[column].astype(str).str.lower() == str(value).lower()]
        
        return df_filtered
