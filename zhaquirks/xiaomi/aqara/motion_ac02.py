"""Quirk for LUMI lumi.motion.ac02."""
import logging
from typing import Any

from zigpy.profiles import zha
from zigpy.quirks import CustomDevice
import zigpy.types as types
from zigpy.zcl.clusters.general import Basic, Identify, Ota, PowerConfiguration

from zhaquirks import Bus
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)
from zhaquirks.xiaomi import (
    IlluminanceMeasurementCluster,
    MotionCluster,
    OccupancyCluster,
    XiaomiAqaraE1Cluster,
    XiaomiPowerConfiguration,
)

_LOGGER = logging.getLogger(__name__)


class OppleCluster(XiaomiAqaraE1Cluster):
    """Opple cluster."""

    ep_attribute = "opple_cluster"
    attributes = {
        0x0102: ("detection_interval", types.uint8_t, True),
        0x010C: ("motion_sensitivity", types.uint8_t, True),
    }

    def _update_attribute(self, attrid: int, value: Any) -> None:
        super()._update_attribute(attrid, value)
        if attrid == 274:
            value = value - 65536
            self.endpoint.illuminance.illuminance_reported(value)
            self.endpoint.occupancy.update_attribute(0, 1)

    async def write_attributes(
        self, attributes: dict[str | int, Any], manufacturer: int | None = None
    ) -> list:
        """Write attributes to device with internal 'attributes' validation."""
        result = await super().write_attributes(attributes, manufacturer)
        interval = attributes.get("detection_interval", attributes.get(0x0102))
        _LOGGER.warning("interval: %s", interval)
        if interval is not None:
            self.endpoint.ias_zone.reset_s = int(interval)
        return result


class LumiMotionAC02(CustomDevice):
    """Lumi lumi.motion.ac02 (RTCGQ14LM) custom device implementation."""

    def __init__(self, *args, **kwargs):
        """Init."""
        self.battery_size = 11
        self.battery_bus = Bus()
        self.illuminance_bus = Bus()
        self.motion_bus = Bus()
        super().__init__(*args, **kwargs)

    signature = {
        MODELS_INFO: [("LUMI", "lumi.motion.ac02")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.OCCUPANCY_SENSOR,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    OppleCluster.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Identify.cluster_id,
                    Ota.cluster_id,
                    OppleCluster.cluster_id,
                ],
            }
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.OCCUPANCY_SENSOR,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    XiaomiPowerConfiguration,
                    Identify.cluster_id,
                    OccupancyCluster,
                    MotionCluster,
                    IlluminanceMeasurementCluster,
                    OppleCluster,
                ],
                OUTPUT_CLUSTERS: [
                    Identify.cluster_id,
                    Ota.cluster_id,
                    OppleCluster,
                ],
            }
        }
    }
