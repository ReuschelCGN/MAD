from typing import List, Optional

from mapadroid.db.DbWrapper import DbWrapper
from mapadroid.db.model import (SettingsArea, SettingsAreaPokestop,
                                SettingsAreaRaidsMitm, SettingsRoutecalc, SettingsAreaInitMitm)
from mapadroid.geofence.geofenceHelper import GeofenceHelper
from mapadroid.route.RouteManagerBase import RouteManagerBase
from mapadroid.route.RouteManagerIV import RouteManagerIV
from mapadroid.route.RouteManagerIdle import RouteManagerIdle
from mapadroid.route.RouteManagerInit import RouteManagerInit
from mapadroid.route.RouteManagerLeveling import RouteManagerLeveling
from mapadroid.route.RouteManagerMon import RouteManagerMon
from mapadroid.route.RouteManagerQuests import RouteManagerQuests
from mapadroid.route.RouteManagerRaids import RouteManagerRaids
from mapadroid.utils.collections import Location
from mapadroid.utils.madGlobals import InitTypes
from mapadroid.worker.WorkerType import WorkerType


class RouteManagerFactory:
    @staticmethod
    def get_routemanager(db_wrapper: DbWrapper, area: SettingsArea, coords: Optional[List[Location]],
                         max_radius: int, max_coords_within_radius: int,
                         geofence_helper: GeofenceHelper, routecalc: SettingsRoutecalc, use_s2: bool = False,
                         s2_level: int = 15,
                         mon_ids_iv: Optional[List[int]] = None) -> RouteManagerBase:
        if area.mode == WorkerType.RAID_MITM.value:
            area: SettingsAreaRaidsMitm = area
            route_manager = RouteManagerRaids(db_wrapper=db_wrapper, area=area, coords=coords, max_radius=max_radius,
                                              max_coords_within_radius=max_coords_within_radius,
                                              geofence_helper=geofence_helper, routecalc=routecalc,
                                              use_s2=use_s2, s2_level=s2_level, mon_ids_iv=mon_ids_iv
                                              )
        elif area.mode == WorkerType.MON_MITM.value:
            route_manager = RouteManagerMon(db_wrapper=db_wrapper, area=area, coords=coords, max_radius=max_radius,
                                            max_coords_within_radius=max_coords_within_radius,
                                            geofence_helper=geofence_helper, routecalc=routecalc,
                                            use_s2=use_s2, s2_level=s2_level,
                                            mon_ids_iv=mon_ids_iv
                                            )
        elif area.mode == WorkerType.IV_MITM.value:
            route_manager = RouteManagerIV(db_wrapper=db_wrapper, area=area, coords=coords, max_radius=max_radius,
                                           max_coords_within_radius=max_coords_within_radius,
                                           geofence_helper=geofence_helper, routecalc=routecalc,
                                           mon_ids_iv=mon_ids_iv
                                           )
        elif area.mode == WorkerType.IDLE.value:
            route_manager = RouteManagerIdle(db_wrapper=db_wrapper, area=area, coords=coords, max_radius=max_radius,
                                             max_coords_within_radius=max_coords_within_radius,
                                             geofence_helper=geofence_helper, routecalc=routecalc,
                                             use_s2=use_s2, s2_level=s2_level, mon_ids_iv=mon_ids_iv
                                             )
        elif area.mode == WorkerType.STOPS.value:
            area: SettingsAreaPokestop = area
            max_coords_within_radius = 9999 if area.level else max_coords_within_radius

            if area.level:
                route_manager = RouteManagerLeveling(db_wrapper=db_wrapper, area=area, coords=coords,
                                                     max_radius=max_radius,
                                                     max_coords_within_radius=max_coords_within_radius,
                                                     geofence_helper=geofence_helper, routecalc=routecalc,
                                                     mon_ids_iv=mon_ids_iv
                                                     )
            else:
                route_manager = RouteManagerQuests(db_wrapper=db_wrapper, area=area, coords=coords,
                                                   max_radius=max_radius,
                                                   max_coords_within_radius=max_coords_within_radius,
                                                   geofence_helper=geofence_helper, routecalc=routecalc,
                                                   mon_ids_iv=mon_ids_iv
                                                   )
        elif area.mode == WorkerType.INIT.value:
            area: SettingsAreaInitMitm = area
            max_radius = max_radius
            if area.init_type == InitTypes.FORTS.value:
                max_radius = 490
            # TODO: Remove magic numbers, move elsewhere...
            route_manager = RouteManagerInit(db_wrapper=db_wrapper, area=area, coords=coords, max_radius=max_radius,
                                             max_coords_within_radius=max_coords_within_radius,
                                             geofence_helper=geofence_helper, routecalc=routecalc,
                                             use_s2=use_s2, s2_level=s2_level, mon_ids_iv=mon_ids_iv
                                             )
        else:
            raise RuntimeError("Invalid mode found in mapping parser.")
        return route_manager
