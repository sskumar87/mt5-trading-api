"""
Date utilities for period-based filtering
"""

from datetime import datetime, timedelta
from typing import Tuple, Optional
import calendar


class PeriodDateConverter:
    """Converts period constants to from_date and to_date ranges"""
    
    VALID_PERIODS = [
        'TODAY', 'YESTERDAY', 'CURR_WEEK', 'LAST_WEEK', 
        'LAST_2_WEEKS', 'CURR_MONTH', 'LAST_MONTH'
    ]
    
    @staticmethod
    def convert_period_to_dates(period: str, reference_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        Convert period constant to from_date and to_date
        
        Args:
            period: Period constant (TODAY, YESTERDAY, etc.)
            reference_date: Reference date for calculations (defaults to now)
            
        Returns:
            Tuple of (from_date, to_date)
            
        Example transformations (assuming today is 8th Sep 2025):
        - TODAY: from_date=8th Sep 00:00:00, to_date=now
        - YESTERDAY: from_date=7th Sep 00:00:00, to_date=7th Sep 23:59:59
        - CURR_WEEK: from_date=nearest previous Monday 00:00:00, to_date=now
        - LAST_WEEK: from_date=Monday of last week 00:00:00, to_date=Sunday of last week 23:59:59
        - LAST_2_WEEKS: from_date=Monday 2 weeks ago 00:00:00, to_date=Sunday last week 23:59:59
        - CURR_MONTH: from_date=1st of current month 00:00:00, to_date=now
        - LAST_MONTH: from_date=1st of last month 00:00:00, to_date=last day of last month 23:59:59
        """
        if period not in PeriodDateConverter.VALID_PERIODS:
            raise ValueError(f"Invalid period: {period}. Valid periods: {PeriodDateConverter.VALID_PERIODS}")
        
        # Use current time as reference if not provided
        if reference_date is None:
            reference_date = datetime.now()
        
        # Get start of day for reference date
        today_start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == 'TODAY':
            return today_start, reference_date
        
        elif period == 'YESTERDAY':
            yesterday_start = today_start - timedelta(days=1)
            yesterday_end = yesterday_start.replace(hour=23, minute=59, second=59, microsecond=999999)
            return yesterday_start, yesterday_end
        
        elif period == 'CURR_WEEK':
            # Find the most recent Monday (or today if it's Monday)
            days_since_monday = reference_date.weekday()  # Monday=0, Sunday=6
            week_start = today_start - timedelta(days=days_since_monday)
            return week_start, reference_date
        
        elif period == 'LAST_WEEK':
            # Find Monday of last week
            days_since_monday = reference_date.weekday()
            this_week_monday = today_start - timedelta(days=days_since_monday)
            last_week_monday = this_week_monday - timedelta(days=7)
            last_week_sunday = last_week_monday + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
            return last_week_monday, last_week_sunday
        
        elif period == 'LAST_2_WEEKS':
            # From Monday 2 weeks ago to Sunday of last week
            days_since_monday = reference_date.weekday()
            this_week_monday = today_start - timedelta(days=days_since_monday)
            two_weeks_ago_monday = this_week_monday - timedelta(days=14)
            last_week_sunday = this_week_monday - timedelta(days=1)
            last_week_sunday = last_week_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return two_weeks_ago_monday, last_week_sunday
        
        elif period == 'CURR_MONTH':
            # From 1st of current month to now
            month_start = reference_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return month_start, reference_date
        
        elif period == 'LAST_MONTH':
            # From 1st of last month to last day of last month
            if reference_date.month == 1:
                # January -> December of previous year
                last_month_start = reference_date.replace(year=reference_date.year-1, month=12, day=1, 
                                                        hour=0, minute=0, second=0, microsecond=0)
            else:
                last_month_start = reference_date.replace(month=reference_date.month-1, day=1, 
                                                        hour=0, minute=0, second=0, microsecond=0)
            
            # Get last day of last month
            _, last_day = calendar.monthrange(last_month_start.year, last_month_start.month)
            last_month_end = last_month_start.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
            
            return last_month_start, last_month_end
    
    @staticmethod
    def get_period_description(period: str, reference_date: Optional[datetime] = None) -> str:
        """Get human-readable description of the period"""
        if reference_date is None:
            reference_date = datetime.now()
        
        from_date, to_date = PeriodDateConverter.convert_period_to_dates(period, reference_date)
        
        descriptions = {
            'TODAY': f"Today ({from_date.strftime('%Y-%m-%d')})",
            'YESTERDAY': f"Yesterday ({from_date.strftime('%Y-%m-%d')})",
            'CURR_WEEK': f"Current week (from {from_date.strftime('%Y-%m-%d')})",
            'LAST_WEEK': f"Last week ({from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')})",
            'LAST_2_WEEKS': f"Last 2 weeks ({from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')})",
            'CURR_MONTH': f"Current month (from {from_date.strftime('%Y-%m-%d')})",
            'LAST_MONTH': f"Last month ({from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')})"
        }
        
        return descriptions.get(period, f"Unknown period: {period}")


# Convenience function for easy import
def convert_period_to_dates(period: str, reference_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """Convenience function to convert period to date range"""
    return PeriodDateConverter.convert_period_to_dates(period, reference_date)