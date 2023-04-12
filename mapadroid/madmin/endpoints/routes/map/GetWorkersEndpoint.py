from typing import Dict, Optional

from mapadroid.db.model import AuthLevel
from mapadroid.madmin.AbstractMadminRootEndpoint import \
    check_authorization_header
from mapadroid.madmin.endpoints.routes.control.AbstractControlEndpoint import \
    AbstractControlEndpoint
from mapadroid.mapping_manager.MappingManager import DeviceMappingsEntry


class GetWorkersEndpoint(AbstractControlEndpoint):
    """
    "/get_workers"
    """

    @check_authorization_header(AuthLevel.MADMIN_ADMIN)
    async def get(self):
        positions = []
        devicemappings: Optional[
            Dict[str, DeviceMappingsEntry]] = await self._get_mapping_manager().get_all_devicemappings()
        for name, device_mapping_entry in devicemappings.items():
            worker = {
                "name": name,
                "lat": device_mapping_entry.last_location.lat,
                "lon": device_mapping_entry.last_location.lng
            }
            positions.append(worker)
        del devicemappings
        resp = await self._json_response(positions)
        del positions
        return resp
