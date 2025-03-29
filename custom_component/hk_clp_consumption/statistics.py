import logging
from datetime import datetime, timezone
from typing import List, Optional
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    StatisticData,
    StatisticMetaData,
)
from homeassistant.const import UnitOfEnergy
from .const import DOMAIN, STAT_ELECTRICITY_USAGE
from .util import Usage, get_statistic_id

_LOGGER = logging.getLogger(__name__)

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
            return False

        # Generate unique statistic ID
        statistic_id = get_statistic_id(entry_id, STAT_ELECTRICITY_USAGE)

        # Prepare statistics data
        statistics_data = []
        cumulative_sum = 0
        for usage in usages:
            if not isinstance(usage, Usage):
                _LOGGER.warning("Invalid usage object: %s", usage)
                continue
                
            statistics_data.append(
                StatisticData(
                    start=usage.date.astimezone(timezone.utc),
                    state=usage.usage,
                    sum=(cumulative_sum := cumulative_sum + usage.usage),
                )
            )

        if not statistics_data:
            _LOGGER.warning("No valid statistics data to insert")
            return False

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
            "Successfully added consumption statistics from %s to %s",
            usages[0].date,
            usages[-1].date
        )
        return True

    except Exception as err:
        _LOGGER.error("Failed to insert statistics: %s", err)
        return False 