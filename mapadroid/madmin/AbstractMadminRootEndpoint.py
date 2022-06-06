import asyncio
import json
from abc import ABC
from functools import wraps
from typing import Any, Optional, List, Dict

from aiohttp import web
from aiohttp.abc import Request
from aiohttp.helpers import sentinel
from aiohttp.typedefs import LooseHeaders, StrOrURL
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from mapadroid.db.DbWrapper import DbWrapper
from mapadroid.db.model import Base
from mapadroid.mad_apk.abstract_apk_storage import AbstractAPKStorage
from mapadroid.madmin import apiException
from mapadroid.mapping_manager.MappingManager import MappingManager
from mapadroid.utils.aiohttp import get_forwarded_path, add_prefix_to_url
from mapadroid.utils.json_encoder import MADEncoder
from mapadroid.utils.madGlobals import WebsocketWorkerTimeoutException, WebsocketWorkerConnectionClosedException
from mapadroid.utils.questGen import QuestGen
from mapadroid.updater.updater import DeviceUpdater
from mapadroid.websocket.WebsocketServer import WebsocketServer


FORWARDED_PATH_KEY = "forwarded_path"


def expand_context() -> Any:
    def wrapper(func):
        @wraps(func)
        async def wrapped(self: AbstractMadminRootEndpoint, *args, **kwargs):
            passed_to_template: Dict = await func(self, *args, **kwargs)
            passed_to_template[FORWARDED_PATH_KEY] = get_forwarded_path(self.request.headers)
            return passed_to_template
        return wrapped
    return wrapper


class AbstractMadminRootEndpoint(web.View, ABC):
    # TODO: Add security etc in here (abstract) to enforce security true/false
    # If we really need more methods, we can just define them abstract...
    def __init__(self, request: Request):
        super().__init__(request)
        self._commit_trigger: bool = False
        self._session: Optional[AsyncSession] = None
        if self._get_mad_args().madmin_time == "12":
            self._datetimeformat = '%Y-%m-%d %I:%M:%S %p'
        else:
            self._datetimeformat = '%Y-%m-%d %H:%M:%S'
        self._identifier = None

    async def _iter(self):
        db_wrapper: DbWrapper = self._get_db_wrapper()
        async with db_wrapper as session, session:
            self._session = session
            with logger.contextualize(identifier=self._get_request_address(), name="madmin-endpoint"):
                response = await self.__generate_response(session)
            return response

    async def __generate_response(self, session: AsyncSession):
        try:
            logger.debug("Waiting for response to {}", self.request.url)
            response = await super()._iter()
            logger.success("Got response to {}", self.request.url)
            if self._commit_trigger:
                logger.debug("Awaiting commit")
                await session.commit()
                logger.info("Done committing")
            else:
                await session.rollback()
        except (WebsocketWorkerTimeoutException, WebsocketWorkerConnectionClosedException) as e:
            logger.warning("Worker was removed or timeout issuing command, unable to process request. {}", e)
            raise web.HTTPInternalServerError
        except web.HTTPFound as e:
            raise e
        except Exception as e:
            logger.warning("Exception occurred in request!. Details: " + str(e))
            logger.exception(e)
            await session.rollback()
            # TODO: Get previous URL...
            raise web.HTTPInternalServerError()
        return response

    def _save(self, instance: Base):
        """
        Creates or updates
        :return:
        """
        self._commit_trigger = True
        self._session.add(instance)
        # await self._session.flush(instance)

    async def _delete(self, instance: Base):
        """
        Deletes the instance from the DB
        :param instance:
        :return:
        """
        self._commit_trigger = True
        await self._session.delete(instance)

    def _get_request_address(self) -> str:
        if "CF-Connecting-IP" in self.request.headers:
            address = self.request.headers["CF-Connecting-IP"]
        elif "X-Forwarded-For" in self.request.headers:
            address = self.request.headers["X-Forwarded-For"]
        else:
            address = self.request.remote
        return address

    async def _add_notice_message(self, message: str) -> None:
        # TODO: Handle accordingly
        # session = await get_session(self.request)
        # session["notice"] = message
        pass

    async def _redirect(self, redirect_to: StrOrURL, commit: bool = False):
        if commit:
            await self._session.commit()
        else:
            await self._session.rollback()
        raise web.HTTPFound(redirect_to)

    def _get_db_wrapper(self) -> DbWrapper:
        return self.request.app['db_wrapper']

    def _get_storage_obj(self) -> AbstractAPKStorage:
        return self.request.app['storage_obj']

    def _get_mad_args(self):
        return self.request.app['mad_args']

    def _get_mapping_manager(self) -> MappingManager:
        return self.request.app['mapping_manager']

    def _get_ws_server(self) -> WebsocketServer:
        return self.request.app['websocket_server']

    def _get_plugin_hotlinks(self) -> List[Dict]:
        return self.request.app["plugin_hotlink"]

    def _get_mon_name_cache(self) -> Dict[int, str]:
        return self.request.app["mon_name_cache"]

    def _get_quest_gen(self) -> QuestGen:
        return self.request.app["quest_gen"]

    @staticmethod
    def _convert_to_json_string(content) -> str:
        try:
            return json.dumps(content, cls=MADEncoder)
        except Exception as err:
            raise apiException.FormattingError(err)

    def _get_instance_id(self) -> int:
        db_wrapper: DbWrapper = self._get_db_wrapper()
        return db_wrapper.get_instance_id()

    def _get_device_updater(self) -> DeviceUpdater:
        return self.request.app['device_updater']

    async def _json_response(self, data: Any = sentinel, *, text: Optional[str] = None, body: Optional[bytes] = None,
                             status: int = 200, reason: Optional[str] = None, headers: Optional[LooseHeaders] = None,
                             content_type: str = "application/json") -> web.Response:
        if data is not sentinel:
            if text or body:
                raise ValueError("only one of data, text, or body should be specified")
            elif data:
                loop = asyncio.get_running_loop()

                text = await loop.run_in_executor(
                    None, self.__json_dumps_proxy, data)
            else:
                # Depending on whether a list or dict is returned... just dumps...
                text = json.dumps(data)
                del data
        return web.Response(
            text=text,
            body=body,
            status=status,
            reason=reason,
            headers=headers,
            content_type=content_type,
        )

    @staticmethod
    def __json_dumps_proxy(data):
        return json.dumps(data, indent=None, cls=MADEncoder)

    def _url_for(self, path_name: str, query: Optional[Dict] = None, dynamic_path: Optional[Dict] = None):
        if dynamic_path is None:
            dynamic_path = {}
        if query is None:
            query = {}
        forwarded_path: Optional[str] = get_forwarded_path(self.request.headers)
        path_constructed = self.request.app.router[path_name].url_for(**dynamic_path).with_query(query)
        final_url = add_prefix_to_url(forwarded_path, path_constructed)
        return final_url
