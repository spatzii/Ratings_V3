import json
import pandas as pd
from pathlib import Path
from datetime import timedelta
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class SlotAveragesCalculator:
    """Calculates and inserts slot averages into ratings report based on day of week."""
    
    DECIMAL_PRECISION = 2
    
    def __init__(self, slots_config_path: Path | str):
        """Initialize with path to time_slots.json configuration.
        
        Args:
            slots_config_path: Path to the JSON file containing slot definitions
        """
        self.slots_config_path = Path(slots_config_path)
        self.slots_config = self._load_slots_config()
        
    def _load_slots_config(self) -> Dict:
        """Load the time slots configuration from JSON file.
        
        Returns:
            Dictionary containing slot definitions for different day patterns
        """
        with open(self.slots_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_slots_for_date(self, date: pd.Timestamp) -> List[Dict]:
        """Get the appropriate slot configuration for a given date.
        
        Args:
            date: The date to get slots for
            
        Returns:
            List of slot dictionaries with start_time and end_time
        """
        weekday = date.weekday()  # 0=Monday, 6=Sunday
        
        if weekday <= 3:  # Monday to Thursday (0-3)
            return self.slots_config['monday_to_thursday']
        elif weekday == 4:  # Friday (4)
            return self.slots_config['friday']
        else:  # Saturday and Sunday (5-6)
            return self.slots_config['saturday_sunday']

    def _calculate_slot_average(self, df: pd.DataFrame, slot: Dict, base_date: pd.Timestamp) -> pd.Series:
        """Calculate average for a single time slot.

        Args:
            df: DataFrame with datetime index and channel columns
            slot: Dictionary with 'start_time', 'end_time', and optional 'next_day' flag
            base_date: The base date for the broadcast day

        Returns:
            Series with average ratings for each channel in the slot
        """
        start_time = slot['start_time']
        end_time = slot['end_time']

        # Determine if slot crosses midnight (e.g., 23:00 - 01:00)
        crosses_midnight = start_time > end_time

        if slot.get('next_day', False):
            if crosses_midnight:
                # Slot like 23:00 - 01:00: start is on base_date, end is on next day
                start_dt = pd.to_datetime(f"{base_date.date()} {start_time}")
                end_dt = pd.to_datetime(f"{base_date.date()} {end_time}") + timedelta(days=1)
            else:
                # Slot like 01:00 - 02:00: both times are on next day
                start_dt = pd.to_datetime(f"{base_date.date()} {start_time}") + timedelta(days=1)
                end_dt = pd.to_datetime(f"{base_date.date()} {end_time}") + timedelta(days=1)

            # Filter data for this slot using datetime range (exclusive of end)
            slot_data = df.loc[start_dt:end_dt - timedelta(minutes=1)]
        else:
            # Regular same-day slot - can use between_time for efficiency
            slot_data = df.between_time(start_time, end_time, inclusive='left')

        if len(slot_data) == 0:
            logger.warning(f"No data found for slot {start_time} - {end_time}")
            return pd.Series(dtype=float)

        # Calculate average
        return slot_data.mean().round(self.DECIMAL_PRECISION)

    @staticmethod
    def _format_slot_label(slot: Dict) -> str:
        """Create a readable label for the slot average row.
        
        Args:
            slot: Dictionary with 'start_time' and 'end_time'
            
        Returns:
            Formatted string like "Slot 06:00 - 07:00"
        """
        return f"MEDIE {slot['start_time']} - {slot['end_time']}"
    
    def insert_slot_averages(self, report_df: pd.DataFrame, original_df: pd.DataFrame) -> pd.DataFrame:
        """Insert slot average rows into the report at appropriate positions.
        
        Args:
            report_df: The report DataFrame with 15-minute intervals
            original_df: The original DataFrame with full minute-by-minute data
            
        Returns:
            DataFrame with slot averages inserted after relevant intervals
        """
        # Get the base date from the original data
        base_date = original_df.index.min().normalize()
        
        # Get slots for this date's day of week
        slots = self._get_slots_for_date(base_date)
        
        # Build a new dataframe with slot averages inserted
        result_rows = []
        
        for i, row in report_df.iterrows():
            # Add the interval row
            result_rows.append((i, row))
            
            # Check if this is the last interval before a slot ends
            if i != 'Average':  # Don't process the overall average row
                current_time = self._parse_interval_end_time(i, base_date)
                
                # Check each slot to see if it ends at this time
                for slot in slots:
                    slot_end = self._parse_slot_time(slot['end_time'], base_date, slot.get('next_day', False))
                    
                    if current_time == slot_end:
                        # Calculate and insert slot average
                        slot_avg = self._calculate_slot_average(original_df, slot, base_date)
                        
                        if not slot_avg.empty:
                            slot_label = self._format_slot_label(slot)
                            result_rows.append((slot_label, slot_avg))
                            logger.info(f"Inserted slot average: {slot_label}")
        
        # Convert back to DataFrame
        result_df = pd.DataFrame([row for _, row in result_rows], 
                                 index=[idx for idx, _ in result_rows])
        
        return result_df
    
    @staticmethod
    def _parse_interval_end_time(interval_label: str, base_date: pd.Timestamp) -> pd.Timestamp:
        """Parse the end time from an interval label like '06:00 - 06:15'.
        
        Args:
            interval_label: String like "06:00 - 06:15"
            base_date: The base date for the broadcast day
            
        Returns:
            Timestamp of the interval end time
        """
        end_time_str = interval_label.split(' - ')[1]
        end_dt = pd.to_datetime(f"{base_date.date()} {end_time_str}")
        
        # Handle intervals that cross midnight
        if end_time_str < "06:00":  # Arbitrary cutoff assuming broadcast day starts at 06:00
            end_dt += timedelta(days=1)
            
        return end_dt
    
    @staticmethod
    def _parse_slot_time(time_str: str, base_date: pd.Timestamp, is_next_day: bool = False) -> pd.Timestamp:
        """Parse a slot time string into a Timestamp.
        
        Args:
            time_str: Time string like "06:00"
            base_date: The base date for the broadcast day
            is_next_day: Whether this time is on the next day
            
        Returns:
            Timestamp of the slot time
        """
        dt = pd.to_datetime(f"{base_date.date()} {time_str}")
        if is_next_day:
            dt += timedelta(days=1)
        return dt


# Example usage and testing
async def main():
    """Example of how to use SlotAveragesCalculator with DailyReportGenerator."""
    from services.daily_report_generator import DailyReportGenerator

    file_path = Path('/Users/stefanpana/PycharmProjects/RatingsBackend/Digi 24-audiente zilnice la minut 2026-01-30.xlsx')
    slots_config = Path('/Users/stefanpana/PycharmProjects/RatingsBackend/core/time_slots.json')

    # Generate the base report
    report_generator = DailyReportGenerator(
        filepath=file_path,
        channels=['Digi 24', 'Antena 3 CNN']
    )
    
    base_report = await report_generator.generate_report()
    
    # Add slot averages
    slot_calculator = SlotAveragesCalculator(slots_config)
    enhanced_report = slot_calculator.insert_slot_averages(
        report_df=base_report,
        original_df=report_generator._dataframe
    )
    
    print(enhanced_report)
    print("\nHTML output:")
    print(enhanced_report.to_html())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
