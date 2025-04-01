import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
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

        # Get last statistics to initialize cumulative sum
        last_stats = await get_instance(hass).async_add_executor_job(
            lambda: get_last_statistics(
                hass,
                statistic_id=statistic_id,
                convert_units=True,
                types={"sum", "start"},
                number_of_stats=1
            )
        )
        cumulative_sum = 0.0
        statistics_data: List[StatisticData] = []

        # Process usages based on last statistics
        if last_stats and statistic_id in last_stats:
            last_stat = last_stats[statistic_id][-1]
            if "sum" in last_stat and "start" in last_stat:
                cumulative_sum = float(last_stat["sum"])
                last_stat_date = datetime.fromtimestamp(
                    last_stat["start"],
                    timezone.utc
                )

                for usage in usages:
                    if usage.date.timestamp() <= last_stat_date.timestamp():
                        _LOGGER.info(
                            "Skipping this record as it's already inserted (last: %s, new: %s)",
                            last_stat_date.timestamp(),
                            usage.date.timestamp()
                        )
                    else:
                        statistics_data.append(
                            StatisticData(
                                start=usage.date.astimezone(timezone.utc),
                                state=usage.usage,
                                sum=(cumulative_sum := cumulative_sum + usage.usage),
                            )
                        )
                        _LOGGER.info(
                            "Added statistic: date=%s, usage=%.2f kWh, cumulative=%.2f kWh",
                            usage.date,
                            usage.usage,
                            cumulative_sum
                        )
            else:
                _LOGGER.warning(
                    "Last statistics missing required fields: %s",
                    last_stat
                )
        else:
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
                _LOGGER.info(
                    "Added statistic: date=%s, usage=%.2f kWh, cumulative=%.2f kWh",
                    usage.date,
                    usage.usage,
                    cumulative_sum
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
            "Successfully added consumption statistics from %s to %s (total sum: %.2f kWh)",
            usages[0].date,
            usages[-1].date,
            cumulative_sum
        )
        return True

    except Exception as err:
        _LOGGER.error("Failed to insert statistics: %s", err)
        return False 