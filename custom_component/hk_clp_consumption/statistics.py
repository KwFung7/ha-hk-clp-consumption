import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    StatisticData,
    StatisticMetaData,
    get_last_statistics,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.recorder import get_instance
from .const import DOMAIN, STAT_ELECTRICITY_USAGE
from .util import Usage, get_statistic_id

_LOGGER = logging.getLogger(__name__)

def create_statistic_data(
    usage: Usage,
    cumulative_sum: float,
) -> Tuple[StatisticData, float]:
    """Create a StatisticData object from a Usage object and update cumulative sum.
    
    Args:
        usage: The Usage object containing consumption data
        cumulative_sum: The current cumulative sum
        
    Returns:
        Tuple[StatisticData, float]: The created statistics data object and updated cumulative sum
    """
    new_sum = cumulative_sum + usage.usage
    return (
        StatisticData(
            start=usage.date.astimezone(timezone.utc),
            state=usage.usage,
            sum=new_sum,
        ),
        new_sum
    )

def process_usage(
    usage: Usage,
    last_stat_date: Optional[datetime],
    cumulative_sum: float,
) -> Tuple[Optional[StatisticData], float]:
    """Process a single usage record.
    
    Args:
        usage: The Usage object to process
        last_stat_date: The date of the last statistic, if any
        cumulative_sum: The current cumulative sum
        
    Returns:
        Tuple[Optional[StatisticData], float]: The processed statistic data (if any) and updated cumulative sum
    """
    if not isinstance(usage, Usage):
        _LOGGER.warning("Invalid usage object: %s", usage)
        return None, cumulative_sum

    if last_stat_date and usage.date.timestamp() <= last_stat_date.timestamp():
        _LOGGER.debug(
            "Skipping record as it's already inserted (last: %s, new: %s)",
            last_stat_date,
            usage.date
        )
        return None, cumulative_sum

    statistic_data, new_sum = create_statistic_data(usage, cumulative_sum)
    _LOGGER.debug(
        "Added statistic: date=%s, usage=%.2f kWh, cumulative=%.2f kWh",
        usage.date,
        usage.usage,
        new_sum
    )
    return statistic_data, new_sum

async def insert_statistics(
    hass,
    entry_id: str,
    name: str,
    usages: List[Usage],
    unit_of_measurement: str = UnitOfEnergy.KILO_WATT_HOUR,
) -> bool:
    """Insert consumption statistics into Home Assistant.
    
    Args:
        hass: Home Assistant instance
        entry_id: The config entry ID
        name: Display name for the statistics
        usages: List of Usage objects containing consumption data
        unit_of_measurement: Unit of measurement (default: kWh)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not usages:
            _LOGGER.warning("No usage data to insert")
            return True

        # Generate unique statistic ID
        statistic_id = get_statistic_id(entry_id, STAT_ELECTRICITY_USAGE)

        # Get last statistics to initialize cumulative sum
        try:
            last_stats = await get_instance(hass).async_add_executor_job(
                lambda: get_last_statistics(
                    hass,
                    statistic_id=statistic_id,
                    convert_units=True,
                    types={"sum", "start"},
                    number_of_stats=1
                )
            )
        except Exception as err:
            _LOGGER.error("Failed to get last statistics: %s", err)
            last_stats = None

        cumulative_sum = 0.0
        last_stat_date = None

        # Initialize from last statistics if available
        if last_stats and statistic_id in last_stats:
            last_stat = last_stats[statistic_id][-1]
            if "sum" in last_stat and "start" in last_stat:
                try:
                    cumulative_sum = float(last_stat["sum"])
                    last_stat_date = datetime.fromtimestamp(
                        last_stat["start"],
                        timezone.utc
                    )
                    _LOGGER.info(
                        "Found last statistics from %s with sum %.2f kWh",
                        last_stat_date,
                        cumulative_sum
                    )
                except (ValueError, TypeError) as err:
                    _LOGGER.error("Error processing last statistics: %s", err)

        # Process all usages
        statistics_data: List[StatisticData] = []
        for usage in usages:
            statistic_data, cumulative_sum = process_usage(
                usage,
                last_stat_date,
                cumulative_sum
            )
            if statistic_data:
                statistics_data.append(statistic_data)

        if not statistics_data:
            _LOGGER.warning("No valid statistics data to insert")
            return True

        # Create metadata for the statistics
        metadata = StatisticMetaData(
            has_mean=False,
            has_sum=True,
            name=name,
            source=DOMAIN,
            statistic_id=statistic_id,
            unit_of_measurement=unit_of_measurement,
        )

        # Add the statistics
        async_add_external_statistics(hass, metadata, statistics_data)
        
        _LOGGER.info(
            "Successfully added consumption statistics from %s to %s (total sum: %.2f kWh)",
            usages[0].date,
            usages[-1].date,
            cumulative_sum
        )
        return True

    except Exception as err:
        _LOGGER.error("Failed to insert statistics: %s", err)
        return False 