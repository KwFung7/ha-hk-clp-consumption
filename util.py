import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import *
from typing import Dict, Any, Optional, List
from .const import DOMAIN
from .hk_clp import Usage

_LOGGER = logging.getLogger(__name__)

def format_date_range() -> tuple[str, str]:
    """Calculate and format date range for API calls."""
    today = datetime.now()
    next_month = today + relativedelta(months=+1)
    return (
        today.strftime("%Y%m01000000"),
        next_month.strftime("%Y%m01000000")
    )

def parse_date(date_str: str) -> datetime:
    """Parse date string from API into datetime object.
    
    Args:
        date_str: Date string from API (format: YYYYMMDDHHmmss)
        
    Returns:
        datetime object
    """
    try:
        # The API returns dates in format YYYYMMDDHHmmss
        return datetime.strptime(date_str, "%Y%m%d%H%M%S")
    except ValueError as err:
        _LOGGER.error("Failed to parse date string '%s': %s", date_str, err)
        raise

def extract_consumption_data(data: Dict[str, Any]) -> List[Usage]:
    """Extract and log consumption data.
    
    Args:
        data: Dictionary containing consumption data from the API.
        
    Returns:
        List of Usage objects containing the consumption data.
    """
    usages: List[Usage] = []
    
    try:
        results = data.get("results", [])
        if not isinstance(results, list):
            _LOGGER.error("Invalid results format: expected list")
            return usages

        for daily_data in results:
            if not isinstance(daily_data, dict):
                _LOGGER.error("Invalid daily data format: expected dict")
                continue

            kwh_total = daily_data.get("kwhTotal")
            start_time = daily_data.get("startDate")
            end_time = daily_data.get("expireDate")
            temperature = daily_data.get("temp")

            if all(record is not None for record in [kwh_total, start_time, end_time, temperature]):
                _LOGGER.info(
                    "Daily consumption: %.2f kWh, Period: %s to %s, Temperature: %.1f°C",
                    float(kwh_total),
                    start_time,
                    end_time,
                    float(temperature)
                )

                # Create Usage object for this record
                usage = Usage(
                    date=parse_date(start_time),
                    usage=float(kwh_total),
                )
                usages.append(usage)
            else:
                _LOGGER.warning("Incomplete daily data: %s", daily_data)

        return usages
    except Exception as err:
        _LOGGER.error("Error processing consumption data: %s", err)
        return usages

def get_statistic_id(entry_id: str, identifier: str) -> str:
    """Format the statistic id.
    
    Args:
        entry_id: The config entry ID.
        identifier: The statistic identifier.
        
    Returns:
        Formatted statistic ID in lowercase.
    """
    return f"{DOMAIN}:{entry_id.lower()}_{identifier}"