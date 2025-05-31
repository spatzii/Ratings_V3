import pandas as pd

def create_dataframe_dict(resampled_data: pd.DataFrame, mean_data: pd.DataFrame) -> dict:
    """Convert resampled time series data and mean values into a nested dictionary structure.

    Args:
        resampled_data: DataFrame containing time-series data with datetime index
        mean_data: DataFrame containing mean values for each TV channel

    Returns:
        dict: A nested dictionary where:
            - Outer keys are column names from the input DataFrame
            - Inner keys are timestamps in 'YYYY-MM-DD HH:MM:SS' format and 'Medie'
            - Values are the corresponding numerical data and mean values (ratings)

    Example:
        >>> df_resampled = pd.DataFrame({'A': [1, 2]}, index=['2025-01-01 12:00:00', '2025-01-01 12:15:00'])
        >>> df_mean = pd.DataFrame({'A': 1.5})
        >>> create_dataframe_dict(df_resampled, df_mean)
        {
            'A': {
                '2025-01-01 12:00:00': 1,
                '2025-01-01 12:15:00': 2,
                'Medie': 1.5
            }
        }
    """
    return {
        column: {
            **{index.strftime('%Y-%m-%d %H:%M:%S'): value
               for index, value in resampled_data[column].items()},
            'Medie': mean_data[column]
        }
        for column in resampled_data.columns
    }

