import asyncio
from typing import Optional

from aiohttp import web
from loguru import logger

from mapadroid.madmin.endpoints.routes.control.AbstractControlEndpoint import \
    AbstractControlEndpoint
from mapadroid.madmin.functions import generate_device_screenshot_path
from mapadroid.mapping_manager.MappingManager import DeviceMappingsEntry


class ClickScreenshotEndpoint(AbstractControlEndpoint):
    """
    "/click_screenshot"
    """

    async def get(self) -> web.Response:
        origin: Optional[str] = self.request.query.get("origin")
        # origin_logger = get_origin_logger(self._logger, origin=origin)
        click_x: Optional[str] = self.request.query.get("clickx")
        click_y: Optional[str] = self.request.query.get("clicky")
        useadb_raw: Optional[str] = self.request.query.get("adb")
        useadb: bool = True if useadb_raw is not None else False
        devicemapping: Optional[DeviceMappingsEntry] = await self._get_mapping_manager().get_devicemappings_of(origin)
        if not devicemapping:
            logger.warning("Device {} not found.", origin)
            return web.Response(text="Failed clearing game data.")
        filename = generate_device_screenshot_path(origin, devicemapping, self._get_mad_args())

        height, width = await self._read_screenshot_size(filename)

        real_click_x = int(width / float(click_x))
        real_click_y = int(height / float(click_y))

        if useadb and await self._adb_connect.make_screenclick(devicemapping.device_settings.adbname, origin,
                                                               real_click_x, real_click_y):
            # TODO: origin_logger.info('MADmin: ADB screenclick successfully')
            pass
        else:
            # TODO: origin_logger.info("MADmin: WS Click x:{}, y:{}", real_click_x, real_click_y)
            temp_comm = self._get_ws_server().get_origin_communicator(origin)
            await temp_comm.click(int(real_click_x), int(real_click_y))

        await asyncio.sleep(2)
        creationdate = await self._take_screenshot()
        return web.Response(text=creationdate)
