from typing import Dict, Optional

from mapadroid.db.helper.SettingsGeofenceHelper import SettingsGeofenceHelper
from mapadroid.db.model import AuthLevel, SettingsGeofence
from mapadroid.geofence.geofenceHelper import GeofenceHelper
from mapadroid.madmin.AbstractMadminRootEndpoint import \
    check_authorization_header
from mapadroid.madmin.endpoints.routes.control.AbstractControlEndpoint import \
    AbstractControlEndpoint


class GetGeofencesEndpoint(AbstractControlEndpoint):
    """
    "/get_geofences"
    """

    @check_authorization_header(AuthLevel.MADMIN_ADMIN)
    async def get(self):
        geofences: Dict[int, SettingsGeofence] = await SettingsGeofenceHelper.get_all_mapped(self._session,
                                                                                             self._get_instance_id())
        export = []
        for geofence_id, geofence in geofences.items():
            geofence_helper: Optional[GeofenceHelper] = await self._get_mapping_manager().get_geofence_helper(
                geofence_id)
            if not geofence_helper:
                continue
            if len(geofence_helper.geofenced_areas) == 1:
                geofenced_area = geofence_helper.geofenced_areas[0]
                if "polygon" in geofenced_area:
                    export.append({
                        "id": geofence_id,
                        "name": geofence.name,
                        "coordinates": geofenced_area["polygon"]
                    })
        del geofences
        resp = await self._json_response(export)
        del export
        return resp
