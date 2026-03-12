"""
Módulo de base de datos PostgreSQL con asyncpg.
"""

import asyncio
import os
from typing import Any

import asyncpg

_pool: asyncpg.Pool | None = None
_lock = asyncio.Lock()


async def connect() -> asyncpg.Pool:
    """Crea y retorna el pool de conexiones a la base de datos de forma segura."""
    global _pool
    async with _lock:
        if _pool is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL no está configurada")
            _pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                timeout=30,
                command_timeout=60,
            )
    return _pool


async def close() -> None:
    """Cierra el pool de conexiones de forma segura."""
    global _pool
    async with _lock:
        if _pool is not None:
            await _pool.close()
            _pool = None


async def execute(
    query: str,
    *args: Any,
) -> str:
    """Ejecuta una consulta SQL y retorna el resultado como string."""
    if _pool is None:
        await connect()
    async with _pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetch(
    query: str,
    *args: Any,
) -> list[asyncpg.Record]:
    """Ejecuta una consulta SELECT y retorna todos los resultados."""
    if _pool is None:
        await connect()
    async with _pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(
    query: str,
    *args: Any,
) -> asyncpg.Record | None:
    """Ejecuta una consulta SELECT y retorna una sola fila o None."""
    if _pool is None:
        await connect()
    async with _pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetchval(
    query: str,
    *args: Any,
) -> Any:
    """Ejecuta una consulta y retorna un solo valor."""
    if _pool is None:
        await connect()
    async with _pool.acquire() as conn:
        return await conn.fetchval(query, *args)


def get_pool() -> asyncpg.Pool | None:
    """Retorna el pool de conexiones actual."""
    return _pool
