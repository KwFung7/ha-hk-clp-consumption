import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import *
from typing import Dict, Any, Optional

_LOGGER = logging.getLogger(__name__)

def format_date_range() -> tuple[str, str]:
    """Calculate and format date range for API calls."""
    today = datetime.now()
    next_month = today + relativedelta(months=+1)
    return (
        today.strftime("%Y%m01000000"),
        next_month.strftime("%Y%m01000000")
    )

def extract_consumption_data(data: Dict[str, Any]) -> None:
    """Extract and log consumption data."""
    try:
        results = data.get("results", [])
        if not isinstance(results, list):
            _LOGGER.error("Invalid results format: expected list")
            return

        for daily_data in results:
            if not isinstance(daily_data, dict):
                _LOGGER.error("Invalid daily data format: expected dict")
                continue

            kwh_total = daily_data.get("kwhTotal")
            start_time = daily_data.get("startDate")
            end_time = daily_data.get("expireDate")
            temperature = daily_data.get("temp")

            if all(v is not None for v in [kwh_total, start_time, end_time, temperature]):
                _LOGGER.info(
                    "Daily consumption: %.2f kWh, Period: %s to %s, Temperature: %.1f°C",
                    float(kwh_total),
                    start_time,
                    end_time,
                    float(temperature)
                )
            else:
                _LOGGER.warning("Incomplete daily data: %s", daily_data)
    except (ValueError, TypeError) as err:
        _LOGGER.error("Error processing consumption data: %s", err)
    except Exception as err:
        _LOGGER.error("Unexpected error processing consumption data: %s", err)