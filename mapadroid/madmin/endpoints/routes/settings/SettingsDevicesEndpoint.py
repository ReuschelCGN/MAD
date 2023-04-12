from typing import Dict, Optional

import aiohttp_jinja2
from aiohttp import web
from aiohttp.abc import Request

from mapadroid.db.helper.SettingsDeviceHelper import SettingsDeviceHelper
from mapadroid.db.helper.SettingsDevicepoolHelper import \
    SettingsDevicepoolHelper
from mapadroid.db.helper.SettingsPogoauthHelper import (LoginType,
                                                        SettingsPogoauthHelper)
from mapadroid.db.helper.SettingsWalkerHelper import SettingsWalkerHelper
from mapadroid.db.model import AuthLevel, SettingsDevice, SettingsPogoauth
from mapadroid.db.resource_definitions.Device import Device
from mapadroid.madmin.AbstractMadminRootEndpoint import (
    AbstractMadminRootEndpoint, check_authorization_header, expand_context)


class SettingsDevicesEndpoint(AbstractMadminRootEndpoint):
    """
    "/settings/devices"
    """

    def __init__(self, request: Request):
        super().__init__(request)

    @check_authorization_header(AuthLevel.MADMIN_ADMIN)
    async def get(self):
        self._identifier: Optional[str] = self.request.query.get("id")
        if self._identifier:
            return await self._render_single_element()
        else:
            return await self._render_overview()

    @aiohttp_jinja2.template('settings_singledevice.html')
    @expand_context()
    async def _render_single_element(self):
        # Parse the mode to send the correct settings-resource definition accordingly
        device: Optional[SettingsDevice] = None
        if self._identifier == "new":
            account_associated = None
            # device = SettingsDevice()
        else:
            device: SettingsDevice = await SettingsDeviceHelper.get(self._session, self._get_instance_id(),
                                                                    int(self._identifier))
            if not device:
                raise web.HTTPFound(self._url_for("settings_devices"))
            # TODO auth: cleanup
            account_associated: Optional[SettingsPogoauth] = await SettingsPogoauthHelper \
                .get_assigned_to_device(self._session, device.device_id)

        settings_vars: Optional[Dict] = self._get_settings_vars()
        ptc_accounts_assigned_or_not_assigned = await SettingsPogoauthHelper.get_avail_accounts(
            self._session, self._get_instance_id(), LoginType.PTC)
        if account_associated:
            ptc_accounts_assigned_or_not_assigned[account_associated.account_id] = account_associated

        available_ggl_accounts: Dict[int, SettingsPogoauth] = await SettingsPogoauthHelper.get_avail_accounts(
            self._session, self._get_instance_id(), LoginType.GOOGLE, return_all_accounts=True)

        template_data: Dict = {
            'identifier': self._identifier,
            'base_uri': self._url_for('api_device'),
            'redirect': self._url_for('settings_devices'),
            'subtab': 'device',
            'element': device,
            'section': device,
            'settings_vars': settings_vars,
            'method': 'POST' if not device else 'PATCH',
            'uri': self._url_for('api_device') if not device else '%s/%s' % (
                self._url_for('api_device'), self._identifier),
            # TODO: Above is pretty generic in theory...
            'ggl_accounts': available_ggl_accounts,
            'ptc_accounts': ptc_accounts_assigned_or_not_assigned,
            'ptc_assigned': account_associated,
            'requires_auth': not self._get_mad_args().autoconfig_no_auth,
            'responsive': str(self._get_mad_args().madmin_noresponsive).lower(),
            'walkers': await SettingsWalkerHelper.get_all_mapped(self._session, self._get_instance_id()),
            'pools': await SettingsDevicepoolHelper.get_all_mapped(self._session, self._get_instance_id()),
        }
        return template_data

    @aiohttp_jinja2.template('settings_devices.html')
    @expand_context()
    async def _render_overview(self):
        template_data: Dict = {
            'base_uri': self._url_for('api_device'),
            'redirect': self._url_for('settings_devices'),
            'subtab': 'device',
            'section': await SettingsDeviceHelper.get_all_mapped(self._session, self._get_instance_id()),
            'walkers': await SettingsWalkerHelper.get_all_mapped(self._session, self._get_instance_id()),
            'pools': await SettingsDevicepoolHelper.get_all_mapped(self._session, self._get_instance_id()),
            'paused': await self._get_mapping_manager().get_paused_devices()
        }
        return template_data

    def _get_settings_vars(self) -> Optional[Dict]:
        return Device.configuration
