"""
Módulo de base de datos PostgreSQL con asyncpg.
"""
import os
from typing import Any, List, Optional
import asyncpg


_pool: Optional[asyncpg.Pool] = None


async def connect() -> asyncpg.Pool:
    """Crea y retorna el pool de conexiones a la base de datos."""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL no está configurada")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
        )
    return _pool


async def close() -> None:
    """Cierra el pool de conexiones."""
    global _pool
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
) -> List[asyncpg.Record]:
    """Ejecuta una consulta SELECT y retorna todos los resultados."""
    if _pool is None:
        await connect()
    async with _pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(
    query: str,
    *args: Any,
) -> Optional[asyncpg.Record]:
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


def get_pool() -> Optional[asyncpg.Pool]:
    """Retorna el pool de conexiones actual."""
    return _pool
