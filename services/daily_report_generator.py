from pathlib import Path
from datetime import timedelta, datetime
import pandas as pd

from utils.logger import get_logger as logger
from services.xlsx_parser import XlsxParser
from services.slot_averages_calculator import SlotAveragesCalculator
from utils.config import current_config

logger = logger(__name__)


class DailyReportGenerator:
    """Generates daily ratings report with 15-minute averages, slot averages, and overall averages.

    This service processes a saved ratings xlsx file and creates a formatted report
    suitable for email delivery. Slot averages are automatically inserted based on
    the day of the week.
    """

    RESAMPLE_INTERVAL = '15min'
    DECIMAL_PRECISION = 2
    REPORT_START_HOUR = 6  # 06:00
    REPORT_END_HOUR = 2  # 02:00 next day

    def __init__(self, filepath: Path, channels: list[str] = None, include_slot_averages: bool = True):
        """Initialize the daily report generator.

        Args:
            filepath: Path to the saved xlsx file
            channels: List of channel names to include in report.
                     Defaults to ['Digi 24', 'Antena 3 CNN']
            include_slot_averages: Whether to include slot averages in the report.
                                   Defaults to True.
        """
        self.filepath = filepath
        self.channels = channels or ['Digi 24', 'Antena 3 CNN']
        self.include_slot_averages = include_slot_averages
        self._dataframe: pd.DataFrame | None = None
        
        # Initialize slot calculator if needed
        if self.include_slot_averages:
            slots_config_path = Path(current_config.PROJECT_ROOT) / 'core' / 'time_slots.json'
            self.slot_calculator = SlotAveragesCalculator(slots_config_path)
        else:
            self.slot_calculator = None

    async def load_and_process(self) -> pd.DataFrame:
        """Load the xlsx file and process it into a pandas DataFrame.

        Returns:
            Processed DataFrame with datetime index and channel columns
        """
        logger.info(f"Loading ratings file: {self.filepath.name}")

        contents = self.filepath.read_bytes()
        parser = XlsxParser(contents, self.filepath.name)
        processed_data = await parser.process_ratings_file()

        # Convert to DataFrame and prepare
        df = pd.DataFrame(processed_data['data'])
        df = df.set_index('Timebands')
        df.index = pd.to_datetime(df.index)

        # Filter to selected channels only
        self._dataframe = df[self.channels]
        logger.info(f"Loaded {len(self._dataframe)} records for {len(self.channels)} channels")

        return self._dataframe

    def _get_broadcast_window(self) -> pd.DataFrame:
        """Extract the broadcast day window (06:00 to 02:00 next day).

        Returns:
            DataFrame filtered to the broadcast window
        """
        if self._dataframe is None:
            raise ValueError("Data not loaded. Call load_and_process() first.")

        start_time = self._dataframe.index.min().normalize() + pd.Timedelta(hours=self.REPORT_START_HOUR)
        # Subtract 1 minute to make end_hour exclusive (e.g., end_hour=1 means up to 00:59, not 01:00)
        end_time = start_time.normalize() + pd.Timedelta(days=1, hours=self._get_report_end_hour()) - pd.Timedelta(minutes=1)

        return self._dataframe.loc[start_time:end_time]

    def _calculate_interval_averages(self, window: pd.DataFrame) -> pd.DataFrame:
        """Calculate 15-minute interval averages.

        Args:
            window: DataFrame containing the broadcast window

        Returns:
            DataFrame with resampled 15-minute averages and formatted index
        """
        quarter_hour_avg = window.resample(self.RESAMPLE_INTERVAL).mean().round(self.DECIMAL_PRECISION)
        return self._rename_index_to_intervals(quarter_hour_avg)

    def _calculate_overall_average(self) -> pd.DataFrame:
        """Calculate the overall average for the full 24-hour broadcast day.

        The "broadcast day" is a fixed, hardcoded 24-hour window defined as:
        **02:00 (inclusive) through 01:59 (inclusive) of the next day**.

        Notes:
            - The overall average is computed from `self._dataframe` using the
              fixed 02:00→01:59 time range.
            - The result is rounded to `DECIMAL_PRECISION` and returned as a single-row
              DataFrame labeled "Average".


        Returns:
            Single-row DataFrame with per-channel overall averages for the 02:00→01:59
            broadcast day.
        """
        overall_avg = self._dataframe.between_time('02:00', '01:59').mean().round(self.DECIMAL_PRECISION)
        overall_avg_df = pd.DataFrame(overall_avg).T
        overall_avg_df.index = ['Whole day']
        return overall_avg_df

    @staticmethod
    def _rename_index_to_intervals(df: pd.DataFrame) -> pd.DataFrame:
        """Rename index to show time intervals (e.g., '06:00 - 06:15').

        Args:
            df: DataFrame with datetime index

        Returns:
            DataFrame with formatted interval labels as index
        """
        time_strings = [idx.strftime('%H:%M') for idx in df.index]

        interval_labels = []
        for start_time in time_strings:
            end_dt = pd.to_datetime(start_time, format='%H:%M') + pd.Timedelta(minutes=15)
            interval_labels.append(f"{start_time} - {end_dt.strftime('%H:%M')}")

        df.index = interval_labels
        return df

    @staticmethod
    def _get_report_end_hour() -> int:
        """Monday-Thursday ends at 1 AM, Friday-Sunday ends at 2 AM.

        Checks yesterday's date since ratings are always for the previous day.
        """
        yesterday = datetime.now() - timedelta(days=1)
        return 1 if yesterday.weekday() <= 3 else 2

    async def generate_report(self) -> pd.DataFrame:
        """Generate the complete daily ratings report.

        Returns:
            DataFrame containing 15-minute intervals, slot averages (if enabled), 
            and overall average
        """
        # Load data if not already loaded
        if self._dataframe is None:
            await self.load_and_process()

        # Get broadcast window
        broadcast_window = self._get_broadcast_window()

        # Calculate interval and overall averages
        interval_averages = self._calculate_interval_averages(broadcast_window)
        overall_average = self._calculate_overall_average()

        # Insert slot averages if enabled
        if self.include_slot_averages and self.slot_calculator:
            logger.info("Inserting slot averages...")
            interval_averages = self.slot_calculator.insert_slot_averages(
                report_df=interval_averages,
                original_df=self._dataframe
            )

        # Combine into final report
        report = pd.concat([interval_averages, overall_average])

        logger.info(f"Generated report with {len(interval_averages)} rows + overall average")
        return report

    # @staticmethod
    # def to_html(report: pd.DataFrame) -> str:
    #     """Convert report to HTML for email delivery.
    #
    #     Args:
    #         report: The generated report DataFrame
    #
    #     Returns:
    #         HTML string representation of the report
    #     """
    #
    #     def highlight_max(row):
    #         """Highlight the maximum value in each row."""
    #         if row.name == 'Whole day':  # Skip highlighting the Whole day row
    #             return [''] * len(row)
    #         # For slot average rows (starting with "MEDIE"), also highlight
    #         max_val = row.max()
    #         return ['background-color: #90EE90' if v == max_val else ''
    #                 for v in row]
    #
    #     styled = report.style.apply(highlight_max, axis=1)
    #     styled = styled.format(precision=2)
    #
    #     return styled.to_html()

    @staticmethod
    def to_html(report: pd.DataFrame) -> str:
        """Convert report to HTML with inline styles for email compatibility."""

        # Start HTML table with inline styles
        html = ['<table style="border-collapse: collapse; font-family: Arial, sans-serif; width: 100%;">',
                '<thead><tr>',
                '<th style="background-color: #4472C4; color: white; padding: 10px; border: 1px solid #ddd;">Time</th>']

        # Header row
        for col in report.columns:
            html.append(
                f'<th style="background-color: #4472C4; color: white; padding: 10px; border: 1px solid #ddd;">{col}</th>')
        html.append('</tr></thead>')

        # Data rows
        html.append('<tbody>')
        for idx, row in report.iterrows():
            html.append('<tr>')

            # Row label cell
            label_style = 'padding: 8px; border: 1px solid #ddd; font-weight: bold;'
            if str(idx).startswith('MEDIE'):
                label_style += ' background-color: #D9E1F2;'  # Light blue - more visible
            html.append(f'<td style="{label_style}">{idx}</td>')

            # Find max value for highlighting (skip certain rows)
            skip_highlight = idx == 'Whole day' or str(idx).startswith('MEDIE')
            max_val = row.max() if not skip_highlight else None

            # Data cells
            for val in row:
                cell_style = 'padding: 8px; text-align: center; border: 1px solid #ddd;'

                # Highlight max value in green
                if max_val is not None and val == max_val:
                    cell_style += ' background-color: #90EE90; font-weight: bold;'
                # MEDIE rows in light blue
                elif str(idx).startswith('MEDIE'):
                    cell_style += ' background-color: #D9E1F2; font-style: italic;'

                html.append(f'<td style="{cell_style}">{val:.2f}</td>')

            html.append('</tr>')
        html.append('</tbody>')
        html.append('</table>')

        return ''.join(html)
    @staticmethod
    def to_string(report: pd.DataFrame) -> str:
        """Convert report to plain text string.

        Args:
            report: The generated report DataFrame

        Returns:
            String representation of the report
        """
        return report.to_string()


# Example usage
async def main():
    """Example of how to use the DailyReportGenerator class."""
    file_path = Path(
        '/Users/stefanpana/PycharmProjects/Ratings_V3/Digi 24-audiente zilnice la minut 2026-02-04.xlsx')

    report_generator = DailyReportGenerator(
        filepath=file_path,
        channels=['Digi 24', 'Antena 3 CNN'],
        include_slot_averages=True
    )

    report = await report_generator.generate_report()
    html_report = report_generator.to_html(report)
    return report, html_report


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
