# voice_data_assistant/app/processing/pandas_processor.py

import pandas as pd
import io
from typing import List, Optional
from app.interfaces.processor_interface import ProcessorInterface
from app.models.intent import Intent
from app.models.result import Result

class PandasProcessor(ProcessorInterface):
    """
    A data processor that uses pandas and is resilient to minor column name variations.
    It acts as a dispatcher, calling specific methods based on the parsed intent.
    """

    def execute(self, intent: Intent, df: pd.DataFrame) -> Result:
        """Dispatcher method to route to the correct private execution method."""
        try:
            df_filtered = self._apply_filters(df, intent.filters)

            operation_map = {
                'sum': self._perform_aggregation,
                'mean': self._perform_aggregation,
                'median': self._perform_aggregation,
                'min': self._perform_aggregation,
                'max': self._perform_aggregation,
                'count': self._perform_aggregation,
                'value_counts': self._perform_aggregation,
                'plot': self._perform_plot,
                'describe': self._perform_describe,
                'info': self._perform_info,
            }

            if intent.operation in operation_map:
                return operation_map[intent.operation](intent, df_filtered)
            else:
                return Result(result_type='error', message=f"Unsupported operation: '{intent.operation}'.")

        except Exception as e:
            return Result(result_type='error', message=str(e))

    def _perform_aggregation(self, intent: Intent, df: pd.DataFrame) -> Result:
        """Handles all single-value and grouped aggregations, including Top N."""
        if not intent.target_column and intent.operation not in ['count', 'value_counts']:
            raise ValueError(f"A target column is required for the '{intent.operation}' operation.")
        
        target_column = self._get_resolved_column(intent.target_column, df.columns) if intent.target_column else None
        group_by_columns = [self._get_resolved_column(col, df.columns) for col in intent.group_by] if intent.group_by else []

        if group_by_columns:
            if intent.operation == 'count':
                agg_result = df.groupby(group_by_columns).size()
            else:
                agg_result = df.groupby(group_by_columns)[target_column].agg(intent.operation)
            
            result_df = agg_result.reset_index(name='result')
            ascending = intent.sort_order == 'asc'
            result_df = result_df.sort_values(by='result', ascending=ascending)

            if intent.limit:
                result_df = result_df.head(intent.limit)
            
            return Result(result_type='table', data=result_df.to_dict(orient='records'), message=intent.description)
        
        else: # No grouping
            if intent.operation == 'count':
                result_val = len(df)
            elif intent.operation == 'value_counts':
                if not target_column: raise ValueError("value_counts requires a target column.")
                result_df = df[target_column].value_counts().reset_index()
                result_df.columns = [target_column, 'count']
                return Result(result_type='table', data=result_df.to_dict(orient='records'), message=intent.description)
            else:
                result_val = df[target_column].agg(intent.operation)
            
            return Result(result_type='value', data=result_val, message=intent.description)

    def _perform_plot(self, intent: Intent, df: pd.DataFrame) -> Result:
        """Handles generating data for plots."""
        if not intent.group_by or not intent.target_column:
            raise ValueError("Plotting requires at least one grouping column and a target column.")
        
        target_column = self._get_resolved_column(intent.target_column, df.columns)
        group_by_columns = [self._get_resolved_column(col, df.columns) for col in intent.group_by]
        
        agg_func = 'sum'
        plot_df = df.groupby(group_by_columns)[target_column].agg(agg_func).reset_index()
        
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
            plot_data={"type": intent.plot_type or 'bar', "data": chart_data}
        )

    def _perform_describe(self, intent: Intent, df: pd.DataFrame) -> Result:
        """Generates descriptive statistics for the dataframe."""
        description = df.describe(include='all').transpose().reset_index()
        description = description.rename(columns={'index': 'column'})
        description = description.fillna('N/A')
        return Result(result_type='table', data=description.to_dict(orient='records'), message=intent.description)

    def _perform_info(self, intent: Intent, df: pd.DataFrame) -> Result:
        """Generates a concise summary of the dataframe."""
        buffer = io.StringIO()
        df.info(buf=buffer)
        info_str = buffer.getvalue()
        return Result(result_type='value', data=info_str, message=intent.description)

    def _apply_filters(self, df: pd.DataFrame, filters: dict) -> pd.DataFrame:
        """Applies filters to the dataframe."""
        if not filters:
            return df
        
        df_filtered = df.copy()
        for column, value in filters.items():
            resolved_col = self._get_resolved_column(column, df.columns)
            df_filtered = df_filtered[df_filtered[resolved_col].astype(str).str.lower() == str(value).lower()]
        
        return df_filtered
    
    def _get_resolved_column(self, target_name: str, actual_columns: List[str]) -> str:
        """Finds the actual column name that best matches the target name."""
        def normalize(name: str) -> str:
            return name.lower().replace("_", "").replace(" ", "")

        normalized_target = normalize(target_name)
        for col in actual_columns:
            if normalize(col) == normalized_target:
                return col
        raise KeyError(f"Column '{target_name}' could not be found in the dataset.")
