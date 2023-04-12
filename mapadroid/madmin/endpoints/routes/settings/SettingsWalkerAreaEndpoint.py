from typing import Dict, Optional

import aiohttp_jinja2
from aiohttp import web
from aiohttp.abc import Request

from mapadroid.db.helper.SettingsWalkerareaHelper import \
    SettingsWalkerareaHelper
from mapadroid.db.helper.SettingsWalkerHelper import SettingsWalkerHelper
from mapadroid.db.model import (AuthLevel, SettingsArea, SettingsWalker,
                                SettingsWalkerarea)
from mapadroid.madmin.AbstractMadminRootEndpoint import (
    AbstractMadminRootEndpoint, check_authorization_header, expand_context)


class SettingsWalkerAreaEndpoint(AbstractMadminRootEndpoint):
    """
    "/settings/walker/areaeditor"
    """

    def __init__(self, request: Request):
        super().__init__(request)

    @check_authorization_header(AuthLevel.MADMIN_ADMIN)
    async def get(self):
        self._identifier: Optional[str] = self.request.query.get("id")
        if self._identifier:
            return await self._render_single_element()
        else:
            raise web.HTTPFound(self._url_for("settings_walkers"))

    @aiohttp_jinja2.template('settings_walkerarea.html')
    @expand_context()
    async def _render_single_element(self):
        # Parse the mode to send the correct settings-resource definition accordingly
        walker: Optional[SettingsWalker] = None
        if not self._identifier:
            raise web.HTTPFound(self._url_for("settings_walkers"))
        else:
            walker: Optional[SettingsWalker] = await SettingsWalkerHelper.get(self._session, self._get_instance_id(),
                                                                              int(self._identifier))
            if not walker:
                raise web.HTTPFound(self._url_for("settings_walkers"))

        walkerarea_id: Optional[str] = self.request.query.get("walkerarea")
        # Only pull this if its set.  When creating a new walkerarea it will be empty
        walkerarea: Optional[SettingsWalkerarea] = None
        if walkerarea_id is not None:
            walkerarea: Optional[SettingsWalkerarea] = await SettingsWalkerareaHelper.get(self._session,
                                                                                          self._get_instance_id(),
                                                                                          int(walkerarea_id))
        areas: Dict[int, SettingsArea] = await self._get_db_wrapper().get_all_areas(self._session)
        walkertypes = ['coords', 'countdown', 'idle', 'period', 'round', 'timer']

        template_data: Dict = {
            'identifier': self._identifier,
            'base_uri': self._url_for('api_walkerarea'),
            'redirect': self._url_for('settings_walkers'),
            'subtab': 'walker',
            'element': walkerarea,
            'uri': self._url_for('api_walkerarea') if not walkerarea_id else '%s/%s' % (
                self._url_for('api_walkerarea'), walkerarea_id),
            # TODO: Above is pretty generic in theory...
            'walkertypes': walkertypes,
            'areas': areas,
            'walker': walker,
            'walkeruri': self._identifier,
        }
        return template_data
