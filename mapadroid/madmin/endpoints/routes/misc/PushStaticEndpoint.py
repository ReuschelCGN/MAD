import os

from aiofile import async_open
from aiohttp import streamer, web

from mapadroid.db.model import AuthLevel
from mapadroid.madmin.AbstractMadminRootEndpoint import (
    AbstractMadminRootEndpoint, check_authorization_header)
from mapadroid.utils.functions import generate_path


class PushStaticEndpoint(AbstractMadminRootEndpoint):
    """
    "/static/{path}"
    """

    @check_authorization_header(AuthLevel.MADMIN_ADMIN)
    # TODO: The entire endpoint is likely useless considering built-in static functionality...
    async def get(self):
        # TODO: Validate screenshot, otherwise we might be sending whatever....
        file_name = self.request.match_info['path']
        headers = {
            "Content-disposition": "attachment; filename={file_name}".format(file_name=file_name)
        }

        file_path = os.path.join(generate_path('madmin/static'), file_name)

        if not os.path.exists(file_path):
            return web.Response(
                body='File <{file_name}> does not exist'.format(file_name=file_name),
                status=404
            )
        else:
            return web.Response(
                body=self.file_sender(file_path=file_path),
                headers=headers
            )

    @streamer
    async def file_sender(self, writer, file_path=None):
        """
        This function will read large file chunk by chunk and send it through HTTP
        without reading them into memory
        """
        # TODO: Asyncio
        async with async_open(file_path, 'rb') as f:
            chunk = await f.read(2 ** 16)
            while chunk:
                await writer.write(chunk)
                chunk = await f.read(2 ** 16)
