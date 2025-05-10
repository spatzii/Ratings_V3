import pandas as pd
import json

def ratings_read_test(file):
    json_str = file.read_text(encoding='utf-8')
    dataframe = pd.DataFrame(json.loads(json_str)['data'])
    dataframe.set_index('Timebands', inplace=True)

    def fix_broadcast_time(timestr, date_of_file):
        try:
            hour, minute = map(int, timestr.split(':'))
            if hour >= 24:
                # Times like 24:00 or 25:00 are actually the next day
                hour = hour - 24
                next_day = pd.to_datetime(date_of_file) + pd.Timedelta(days=1)
                return f'{next_day.strftime("%Y-%m-%d")} {hour:02d}:{minute:02d}'
            return f'{date_of_file} {hour:02d}:{minute:02d}'
        except:
            return None

    def rename_columns(df, string_to_remove):
        new_columns = {col: col.replace(string_to_remove, '') for col in df.columns}
        return df.rename(columns=new_columns)

    file_date = file.stem  # '2025-05-02'
    dataframe.index = pd.to_datetime([fix_broadcast_time(idx, file_date) for idx in dataframe.index])
    # dataframe.index = pd.Index(['Whole day' if pd.isna(idx) else idx for idx in dataframe.index])
    dataframe = dataframe[~dataframe.index.isna()]
    dataframe = rename_columns(dataframe, '.1')

    jds = dataframe.loc['2025-05-07 20:00:00':'2025-05-07 22:59:00', 'Digi 24'].resample('15min').mean().round(2)
    print(jds)
    print(jds.mean().round(2))