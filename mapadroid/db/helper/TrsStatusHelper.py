from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from mapadroid.db.model import TrsStatus
from mapadroid.utils.DatetimeWrapper import DatetimeWrapper
from mapadroid.utils.collections import Location
from mapadroid.utils.logging import LoggerEnums, get_logger

logger = get_logger(LoggerEnums.database)


# noinspection PyComparisonWithNone
class TrsStatusHelper:
    @staticmethod
    async def get(session: AsyncSession, device_id: int) -> Optional[TrsStatus]:
        stmt = select(TrsStatus).where(TrsStatus.device_id == device_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_all_of_instance(session: AsyncSession, instance_id: int) -> List[TrsStatus]:
        """
        DbWrapper::download_status
        Args:
            session:
            instance_id:

        Returns:

        """
        stmt = select(TrsStatus).where(TrsStatus.instance_id == instance_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def reset_status(session: AsyncSession, instance_id: int, device_id: int) -> None:
        status: Optional[TrsStatus] = await TrsStatusHelper.get(session, device_id)
        if not status:
            status = TrsStatus()
            status.device_id = device_id
            status.instance_id = instance_id
        status.globalrebootcount = 0
        status.globalrestartcount = 0
        status.lastPogoReboot = DatetimeWrapper.fromtimestamp(0)
        status.lastPogoRestart = DatetimeWrapper.fromtimestamp(0)
        session.add(status)

    @staticmethod
    async def save_last_reboot(session: AsyncSession, instance_id: int, device_id: int) -> None:
        """
        DbWrapper::save_last_reboot
        Args:
            session:
            instance_id:
            device_id:

        Returns:

        """
        status: Optional[TrsStatus] = await TrsStatusHelper.get(session, device_id)
        if not status:
            status = TrsStatus()
            status.device_id = device_id
            status.instance_id = instance_id
            status.globalrebootcount = 0
        else:
            status.globalrebootcount += 1
        status.lastPogoReboot = DatetimeWrapper.now()
        status.restartCounter = 0
        status.rebootCounter = 0
        session.add(status)

    @staticmethod
    async def save_last_restart(session: AsyncSession, instance_id: int, device_id: int) -> None:
        """
        DbWrapper::save_last_restart
        Args:
            session:
            instance_id:
            device_id:

        Returns:

        """
        status: Optional[TrsStatus] = await TrsStatusHelper.get(session, device_id)
        if not status:
            status = TrsStatus()
            status.device_id = device_id
            status.instance_id = instance_id
            status.globalrestartcount = 0
        else:
            status.globalrestartcount += 1
        status.lastPogoRestart = DatetimeWrapper.now()
        status.restartCounter = 0
        session.add(status)

    @staticmethod
    async def save_idle_status(session: AsyncSession, instance_id: int, device_id: int, idle_state: int) -> None:
        """
        DbWrapper::save_idle_status
        Args:
            idle_state:
            session:
            instance_id:
            device_id:

        Returns:

        """
        status: Optional[TrsStatus] = await TrsStatusHelper.get(session, device_id)
        if not status:
            status = TrsStatus()
            status.device_id = device_id
            status.instance_id = instance_id
        status.idle = idle_state
        session.add(status)

    @staticmethod
    async def set_last_softban_action(session: AsyncSession, instance_id: int, device_id: int,
                                      location: Location,
                                      timestamp: Optional[int] = None) -> None:
        status: Optional[TrsStatus] = await TrsStatusHelper.get(session, device_id)
        if not status:
            status = TrsStatus()
            status.device_id = device_id
            status.instance_id = instance_id
        if timestamp:
            status.last_softban_action = DatetimeWrapper.fromtimestamp(timestamp)
        else:
            status.last_softban_action = DatetimeWrapper.now()
        status.last_softban_action_location = (location.lat, location.lng)
        session.add(status)
