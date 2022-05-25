from typing import AsyncGenerator, Optional, Tuple

from aiohttp import web
from loguru import logger

from mapadroid.mad_apk.utils import stream_package
from mapadroid.mitm_receiver.endpoints.AbstractMitmReceiverRootEndpoint import \
    AbstractMitmReceiverRootEndpoint


class MadApkDownloadEndpoint(AbstractMitmReceiverRootEndpoint):
    """
    "/mad_apk/<string:apk_type>/download"
    "/mad_apk/<string:apk_type>/<string:apk_arch>/download"
    """

    # TODO: Auth/preprocessing for autoconfig?
    async def head(self):
        data_generator, response = await self.__handle_download_request()
        return response

    async def get(self):
        data_generator, response = await self.__handle_download_request()
        async for data in data_generator:
            await response.write(data)
        return response

    async def __handle_download_request(self):
        parsed = self._parse_frontend()
        apk_type, apk_arch = parsed
        response = web.StreamResponse()
        streaming_package: Optional[Tuple[AsyncGenerator, str, str, str]] = await stream_package(self._session,
                                                                                                 self._get_storage_obj(),
                                                                                                 apk_type, apk_arch)
        if not streaming_package:
            raise web.HTTPNotFound()
        else:
            data_generator, mimetype, filename, version = streaming_package
        origin = self.request.headers.get("origin")
        with logger.contextualize(identifier=origin, name="mad_apk_download"):
            logger.info(f"Download of {apk_type}@{apk_arch} requested")
        response.content_type = mimetype
        response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        response.headers['APK-Version'] = '{}'.format(version)
        await response.prepare(self.request)
        return data_generator, response
