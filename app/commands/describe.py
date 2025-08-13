import pandas as pd
from pydantic import BaseModel
from app.commands.base import CommandInterface, CommandParams
from app.models.result import Result

class DescribeCommandParams(CommandParams):
    pass

class DescribeCommand(CommandInterface):
    name = "describe_data"
    description = "Provides a statistical summary (mean, std, etc.) of the numerical columns and counts for categorical columns in the dataset. Use this for general overview questions about the data's properties."
    trigger_words = ["describe", "summary", "statistics", "overview"]
    pydantic_model = DescribeCommandParams

    def execute(self, params: DescribeCommandParams, df: pd.DataFrame) -> Result:
        description_df = df.describe(include='all').transpose().reset_index()
        description_df = description_df.rename(columns={'index': 'column'})
        description_df = description_df.fillna('N/A')
        return Result(
            result_type='table',
            data=description_df.to_dict(orient='records'),
            message="Successfully described the dataset."
        )
