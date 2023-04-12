import os
from typing import Dict, List, Optional

import aiohttp_jinja2
from aiohttp import web
from aiohttp.abc import Request

from mapadroid.db.helper.SettingsMonivlistHelper import SettingsMonivlistHelper
from mapadroid.db.model import AuthLevel, SettingsMonivlist
from mapadroid.db.resource_definitions.MonIvList import MonIvList
from mapadroid.madmin.AbstractMadminRootEndpoint import (
    AbstractMadminRootEndpoint, check_authorization_header, expand_context)
from mapadroid.utils.language import i8ln, open_json_file


class SettingsIvlistsEndpoint(AbstractMadminRootEndpoint):
    """
    "/settings/monivlists"
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

    @aiohttp_jinja2.template('settings_singleivlist.html')
    @expand_context()
    async def _render_single_element(self):
        # Parse the mode to send the correct settings-resource definition accordingly
        monivlist: Optional[SettingsMonivlist] = None
        if self._identifier == "new":
            pass
        else:
            monivlist: SettingsMonivlist = await SettingsMonivlistHelper.get_entry(self._session,
                                                                                   self._get_instance_id(),
                                                                                   int(self._identifier))
            if not monivlist:
                raise web.HTTPFound(self._url_for("settings_ivlists"))

        settings_vars: Optional[Dict] = self._get_settings_vars()

        try:
            current_mons: Optional[List[int]] = await SettingsMonivlistHelper.get_list(self._session,
                                                                                       self._get_instance_id(),
                                                                                       int(self._identifier))
        except Exception:
            current_mons = []
        all_pokemon = await self.get_pokemon()
        mondata = all_pokemon['mondata']
        current_mons_list = []
        for mon_id in current_mons:
            try:
                mon_name = await i8ln(mondata[str(mon_id)]["name"])
            except KeyError:
                mon_name = "No-name-in-file-please-fix"
            current_mons_list.append({"mon_name": mon_name, "mon_id": str(mon_id)})

        template_data: Dict = {
            'identifier': self._identifier,
            'base_uri': self._url_for('api_monivlist'),
            'redirect': self._url_for('settings_ivlists'),
            'subtab': 'monivlist',
            'element': monivlist,
            'section': monivlist,
            'settings_vars': settings_vars,
            'method': 'POST' if not monivlist else 'PATCH',
            'uri': self._url_for('api_monivlist') if not monivlist else '%s/%s' % (
                self._url_for('api_monivlist'), self._identifier),
            # TODO: Above is pretty generic in theory...
            'current_mons_list': current_mons_list
        }
        return template_data

    @aiohttp_jinja2.template('settings_ivlists.html')
    @expand_context()
    async def _render_overview(self):
        template_data: Dict = {
            'base_uri': self._url_for('api_monivlist'),
            'redirect': self._url_for('settings_ivlists'),
            'subtab': 'monivlist',
            'section': await SettingsMonivlistHelper.get_entries_mapped(self._session, self._get_instance_id()),
        }
        return template_data

    def _get_settings_vars(self) -> Optional[Dict]:
        return MonIvList.configuration

    async def get_pokemon(self):
        mondata = await open_json_file('pokemon')
        # Why o.O
        stripped_mondata = {}
        for mon_id in mondata:
            stripped_mondata[mondata[str(mon_id)]["name"]] = mon_id
            if os.environ['LANGUAGE'] != "en":
                try:
                    localized_name = await i8ln(mondata[str(mon_id)]["name"])
                    stripped_mondata[localized_name] = mon_id
                except KeyError:
                    pass
        return {
            'mondata': mondata,
            'locale': stripped_mondata
        }
