import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import *
from typing import Dict, Any, Optional, List
from .const import DOMAIN
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

@dataclass
class Usage:
    """Data class for storing electricity usage data."""
    date: datetime
    usage: float

def format_date_range() -> tuple[str, str]:
    """Calculate and format date range for API calls."""
    today = datetime.now()
    next_month = today + relativedelta(months=+1)
    return (
        today.strftime("%Y%m01000000"),
        next_month.strftime("%Y%m01000000")
    )

def parse_date(date_str: str) -> datetime:
    """Parse date string from API response.
    
    Args:
        date_str: Date string in YYYYMMDDHHmmss format
        
    Returns:
        datetime: Parsed datetime object
        
    Raises:
        ValueError: If date string cannot be parsed
    """
    try:
        return datetime.strptime(date_str, "%Y%m%d%H%M%S")
    except ValueError as err:
        _LOGGER.error("Failed to parse date string '%s': %s", date_str, err)
        raise

def extract_consumption_data(data: Dict[str, Any]) -> List[Usage]:
    """Extract consumption data from API response.
    
    Args:
        data: API response data containing consumption records
        
    Returns:
        List[Usage]: List of Usage objects containing date and consumption values
        
    Raises:
        ValueError: If data is invalid or missing required fields
    """
    usages: List[Usage] = []
    
    try:
        results = data.get("results", [])
        if not results:
            _LOGGER.warning("No consumption records found in API response")
            return usages
            
        for record in results:
            try:
                start_time = record.get("startDate")
                if not start_time:
                    _LOGGER.warning("Record missing startDate field: %s", record)
                    continue
                    
                kwh_total = record.get("kwhTotal")
                if not kwh_total:
                    _LOGGER.warning("Record missing kwhTotal field: %s", record)
                    continue
                    
                try:
                    usage_value = float(kwh_total)
                except ValueError:
                    _LOGGER.warning("Invalid kwhTotal value '%s' in record: %s", kwh_total, record)
                    continue
                    
                usages.append(Usage(
                    date=parse_date(start_time),
                    usage=usage_value
                ))
            except Exception as err:
                _LOGGER.warning("Failed to process record %s: %s", record, err)
                continue
                
        if not usages:
            _LOGGER.warning("No valid consumption records found in API response")
            
        return usages
        
    except Exception as err:
        _LOGGER.error("Failed to extract consumption data: %s", err)
        raise

def get_statistic_id(entry_id: str, identifier: str) -> str:
    """Format the statistic id.
    
    Args:
        entry_id: The config entry ID.
        identifier: The statistic identifier.
        
    Returns:
        Formatted statistic ID in lowercase.
    """
    return f"{DOMAIN}:{entry_id.lower()}_{identifier}"