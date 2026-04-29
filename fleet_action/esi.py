"""
ESI helper for fleet-action plugin.

Token strategy:
  - Accepts a character_id; queries Helm's 'characters' table for the stored
    access_token + refresh_token via db_session_factory.
  - If token_expires_at is in the past (or None), calls oauth.refresh_access_token()
    and writes the new tokens back before proceeding.
  - GET calls delegate to app.esi.client.get_esi_client() which handles ETag
    caching, retry, and error-limit awareness.
  - PUT calls (fleet MOTD update) use httpx.AsyncClient directly since
    ESIClient only exposes GET.

ESI scopes required:
  esi-fleets.read_fleet.v1   — read fleet info and members
  esi-fleets.write_fleet.v1  — update fleet MOTD
"""

from datetime import UTC, datetime, timedelta

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.esi.client import get_esi_client
from app.esi.oauth import refresh_access_token
from app.models.character import Character

ESI_BASE = "https://esi.evetech.net/latest"
REQUIRED_SCOPES = {"esi-fleets.read_fleet.v1", "esi-fleets.write_fleet.v1"}


async def get_valid_token(character_id: int, db: AsyncSession) -> tuple[str, str]:
    """
    Return (access_token, refresh_token) for the given character_id.
    Refreshes if expired and persists new tokens to DB.
    Raises HTTP 404 if character not in Helm DB.
    Raises HTTP 403 if character lacks required ESI scopes.
    """
    result = await db.execute(
        select(Character).where(Character.character_id == character_id)
    )
    char = result.scalar_one_or_none()
    if char is None:
        raise HTTPException(
            status_code=404,
            detail=f"角色 {character_id} 未在 Helm 数据库中找到，请先通过 EVE SSO 登录"
        )

    granted = set(char.scopes.split()) if char.scopes else set()
    missing = REQUIRED_SCOPES - granted
    if missing:
        raise HTTPException(
            status_code=403,
            detail=f"角色 {character_id} 缺少必要的 ESI 授权范围：{', '.join(sorted(missing))}。请重新通过 EVE SSO 授权"
        )

    now = datetime.now(UTC)
    exp = char.token_expires_at
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    needs_refresh = exp is None or exp <= now

    if needs_refresh:
        new_tokens = await refresh_access_token(char.refresh_token)
        char.access_token = new_tokens["access_token"]
        char.refresh_token = new_tokens.get("refresh_token", char.refresh_token)
        if "expires_in" in new_tokens:
            char.token_expires_at = now + timedelta(seconds=new_tokens["expires_in"])
        await db.commit()

    return char.access_token, char.refresh_token


async def get_character_fleet(character_id: int, token: str, refresh_token: str) -> dict:
    """GET /characters/{character_id}/fleet — 返回 FC 当前所在舰队信息"""
    client = get_esi_client()
    return await client.get(
        f"/characters/{character_id}/fleet",
        token=token,
        refresh_token=refresh_token,
        character_id=character_id,
    )


async def get_fleet_info(fleet_id: int, token: str, refresh_token: str, character_id: int) -> dict:
    """GET /fleets/{fleet_id} — 返回舰队详情（含 MOTD）"""
    client = get_esi_client()
    return await client.get(
        f"/fleets/{fleet_id}",
        token=token,
        refresh_token=refresh_token,
        character_id=character_id,
    )


async def get_fleet_members(
    fleet_id: int, token: str, refresh_token: str, character_id: int
) -> list[dict]:
    """GET /fleets/{fleet_id}/members — 返回所有舰队成员列表"""
    client = get_esi_client()
    return await client.get(
        f"/fleets/{fleet_id}/members",
        token=token,
        refresh_token=refresh_token,
        character_id=character_id,
    )


async def get_fleet_wings(
    fleet_id: int, token: str, refresh_token: str, character_id: int
) -> list[dict]:
    """GET /fleets/{fleet_id}/wings — 返回舰队编队结构（wing/squad）"""
    client = get_esi_client()
    return await client.get(
        f"/fleets/{fleet_id}/wings",
        token=token,
        refresh_token=refresh_token,
        character_id=character_id,
    )


async def put_fleet_motd(fleet_id: int, token: str, motd: str) -> None:
    """
    PUT /fleets/{fleet_id} — 更新舰队 MOTD。
    ESIClient 不支持 PUT，故直接使用 httpx。
    Raises httpx.HTTPStatusError on non-2xx response.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{ESI_BASE}/fleets/{fleet_id}/",
            json={"motd": motd},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "helm-plugin-fleet-action/0.1.0 (Helm EVE Fleet Manager)",
            },
        )
        resp.raise_for_status()
