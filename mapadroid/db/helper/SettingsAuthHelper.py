from typing import Dict, List, Optional

from aiocache import cached
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from mapadroid.db.model import AuthLevel, SettingsAuth


class SettingsAuthHelper:
    @staticmethod
    async def get(session: AsyncSession, instance_id: int, auth_id: int) -> Optional[SettingsAuth]:
        stmt = select(SettingsAuth).where(and_(SettingsAuth.instance_id == instance_id,
                                               SettingsAuth.auth_id == auth_id))
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_all(session: AsyncSession, instance_id: int) -> List[SettingsAuth]:
        stmt = select(SettingsAuth).where(SettingsAuth.instance_id == instance_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_mapped(session: AsyncSession, instance_id: int) -> Dict[int, SettingsAuth]:
        listed: List[SettingsAuth] = await SettingsAuthHelper.get_all(session, instance_id)
        mapped: Dict[int, SettingsAuth] = {}
        for auth in listed:
            mapped[auth.auth_id] = auth
        return mapped

    @staticmethod
    @cached(ttl=300)
    async def get_auths_for_auth_level(session: AsyncSession, instance_id: int,
                                       auth_level: AuthLevel) -> Dict[str, SettingsAuth]:
        """
        Cached for 5 minutes
        Args:
            session:
            instance_id:
            auth_level:

        Returns: Dict mapping username to the auth entry

        """
        all_auths: List[SettingsAuth] = await SettingsAuthHelper.get_all(session, instance_id)
        return {auth.username: auth for auth in all_auths if auth.auth_level & auth_level.value}
