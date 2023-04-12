from typing import Dict, List, Optional, Set

from aiohttp import web
from loguru import logger

from mapadroid.db.helper.SettingsDeviceHelper import SettingsDeviceHelper
from mapadroid.db.helper.SettingsPogoauthHelper import (LoginType,
                                                        SettingsPogoauthHelper)
from mapadroid.db.helper.TrsVisitedHelper import TrsVisitedHelper
from mapadroid.db.model import (AuthLevel, Base, SettingsDevice,
                                SettingsPogoauth)
from mapadroid.db.resource_definitions.Device import Device
from mapadroid.madmin.AbstractMadminRootEndpoint import \
    check_authorization_header
from mapadroid.madmin.endpoints.api.resources.AbstractResourceEndpoint import \
    AbstractResourceEndpoint


class DeviceEndpoint(AbstractResourceEndpoint):
    async def _delete_connected_post(self, db_entry):
        pass

    async def _delete_connected_prior(self, db_entry):
        assigned_to_device: Optional[SettingsPogoauth] = await SettingsPogoauthHelper \
            .get_assigned_to_device(self._session, db_entry.device_id)
        if assigned_to_device:
            assigned_to_device.device_id = None

    async def _handle_additional_keys(self, db_entry: SettingsDevice, key: str, value) -> bool:
        if key == "ggl_login_mail":
            # just store the value with comma separation
            db_entry.ggl_login_mail = value
            return True
        elif key == "walker":
            db_entry.walker_id = int(value)
            return True
        return False

    def _attributes_to_ignore(self) -> Set[str]:
        return {"device_id", "guid"}

    async def _fetch_all_from_db(self, **kwargs) -> Dict[int, Base]:
        return await SettingsDeviceHelper.get_all_mapped(self._session, self._get_instance_id())

    def _resource_info(self, obj: Optional[Base] = None) -> Dict:
        return Device.configuration

    # TODO: '%s/<string:identifier>' optionally at the end of the route
    # TODO: ResourceEndpoint class that loads the identifier accordingly before patch/post etc are called (populate_mode)

    @check_authorization_header(AuthLevel.MADMIN_ADMIN)
    async def post(self) -> web.Response:
        identifier = self.request.match_info.get('identifier', None)
        api_request_data = await self.request.json()
        # TODO: if not identifier
        if self.request.content_type == 'application/json-rpc':
            if not identifier:
                return await self._json_response(self.request.method, status=405)
            device: Optional[SettingsDevice] = await SettingsDeviceHelper.get(self._session, self._get_instance_id(),
                                                                              int(identifier))
            try:
                if not device:
                    return await self._json_response(dict(), status=404)
                call = api_request_data['call']
                args = api_request_data.get('args', {})
                if call == 'device_state':
                    active = args.get('active', 1)
                    self._get_mapping_manager().set_device_state(int(identifier), active)
                    # TODO:..
                    # self._get_mapping_manager().device_set_disabled(device.name)
                    await self._get_ws_server().force_cancel_worker(device.name)
                    return await self._json_response(dict(), status=200)
                elif call == 'flush_level':
                    username: Optional[str] = await self._get_account_handler().get_assigned_username(
                        device_id=device.device_id)
                    if username:
                        await TrsVisitedHelper.flush_all_of_username(self._session, username)
                        self._commit_trigger = True
                        return await self._json_response(dict(), status=204)
                    else:
                        logger.warning("Failed to retrieve username to clear trs_visited")
                        return await self._json_response("Failed to retrieve username assigned to device to clear "
                                                         "trs_visited.", status=501)
                else:
                    return await self._json_response(call, status=501)
            except KeyError:
                return await self._json_response("Invalid key found in request.", status=501)
        else:
            return await super().post()

    # TODO: Fetch & create should accept kwargs for primary keys consisting of multiple columns
    async def _fetch_from_db(self, identifier, **kwargs) -> Optional[Base]:
        device: Optional[SettingsDevice] = await SettingsDeviceHelper.get(self._session, self._get_instance_id(),
                                                                          identifier)
        return device

    async def _create_instance(self, identifier):
        device = SettingsDevice()
        device.instance_id = self._get_instance_id()
        device.device_id = identifier
        return device
