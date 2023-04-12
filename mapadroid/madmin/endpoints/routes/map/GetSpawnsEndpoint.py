import asyncio
import time
from typing import Dict, List, Optional, Tuple

from mapadroid.db.helper.TrsSpawnHelper import TrsSpawnHelper
from mapadroid.db.model import AuthLevel, TrsEvent, TrsSpawn
from mapadroid.madmin.AbstractMadminRootEndpoint import (
    AbstractMadminRootEndpoint, check_authorization_header)
from mapadroid.madmin.functions import get_bound_params
from mapadroid.utils.collections import Location


class GetSpawnsEndpoint(AbstractMadminRootEndpoint):
    """
    "/get_spawns"
    """

    @check_authorization_header(AuthLevel.MADMIN_ADMIN)
    async def get(self):
        ne_lat, ne_lng, sw_lat, sw_lng, o_ne_lat, o_ne_lng, o_sw_lat, o_sw_lng = get_bound_params(self._request)
        timestamp: Optional[int] = self._request.query.get("timestamp")
        if timestamp:
            timestamp = int(timestamp)

        coords: Dict[str, List[Dict]] = {}
        data: Dict[int, Tuple[TrsSpawn, TrsEvent]] = \
            await TrsSpawnHelper.download_spawns(self._session,
                                                 ne_corner=Location(ne_lat, ne_lng), sw_corner=Location(sw_lat, sw_lng),
                                                 old_ne_corner=Location(o_ne_lat, o_ne_lng),
                                                 old_sw_corner=Location(o_sw_lat, o_sw_lng),
                                                 timestamp=timestamp)
        loop = asyncio.get_running_loop()
        cluster_spawns = await loop.run_in_executor(
            None, self.__serialize_spawns, coords, data)
        del data
        resp = await self._json_response(cluster_spawns)
        del cluster_spawns
        return resp

    @staticmethod
    def get_time_ms():
        return int(time.time() * 1000)

    def __serialize_spawns(self, coords, data):
        # TODO: Starmap/multiprocess if possible given the possible huge amount of data here?
        for (spawn_id, (spawn, event)) in data.items():
            if event.event_name not in coords:
                coords[event.event_name] = []
            coords[event.event_name].append({
                "id": spawn_id,
                "endtime": spawn.calc_endminsec,
                "lat": spawn.latitude,
                "lon": spawn.longitude,
                "spawndef": spawn.spawndef,
                "lastnonscan": spawn.last_non_scanned.strftime(
                    self._datetimeformat) if spawn.last_non_scanned else None,
                "lastscan": spawn.last_scanned.strftime(self._datetimeformat) if spawn.last_scanned else None,
                "first_detection": spawn.first_detection.strftime(self._datetimeformat),
                "event": event.event_name
            })
        cluster_spawns = []
        for spawn in coords:
            cluster_spawns.append({"EVENT": spawn, "Coords": coords[spawn]})
        return cluster_spawns
