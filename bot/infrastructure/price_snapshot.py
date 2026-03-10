"""
Price Snapshot Repository for tracking historical prices per user.

Used to compare current prices with previous snapshots and show
price trend indicators (🔺/🔻/▫️) in the /ver command.
"""

from bot.core import database


class PriceSnapshotRepository:
    """Repository for user price snapshots."""

    async def get_user_snapshots(self, user_id: int) -> dict[str, float]:
        """
        Get the last recorded price snapshots for a user.

        Args:
            user_id: The Telegram user ID.

        Returns:
            Dictionary mapping symbol to price (e.g., {"BTC": 50000.0}).
        """
        records = await database.fetch(
            """
            SELECT symbol, price
            FROM user_price_snapshots
            WHERE user_id = $1
            """,
            user_id,
        )
        return {r["symbol"]: float(r["price"]) for r in records} if records else {}

    async def update_snapshots(self, user_id: int, prices: dict[str, float]) -> None:
        """
        Update price snapshots for a user.

        Args:
            user_id: The Telegram user ID.
            prices: Dictionary mapping symbol to price.
        """
        for symbol, price in prices.items():
            await database.execute(
                """
                INSERT INTO user_price_snapshots (user_id, symbol, price)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, symbol) DO UPDATE SET
                    price = EXCLUDED.price,
                    updated_at = NOW()
                """,
                user_id,
                price,
                symbol,
            )

    async def get_snapshot_for_symbol(self, user_id: int, symbol: str) -> float | None:
        """
        Get the last recorded price for a specific symbol.

        Args:
            user_id: The Telegram user ID.
            symbol: The cryptocurrency symbol (e.g., "BTC").

        Returns:
            The last recorded price or None if not found.
        """
        record = await database.fetchrow(
            """
            SELECT price
            FROM user_price_snapshots
            WHERE user_id = $1 AND symbol = $2
            """,
            user_id,
            symbol,
        )
        return float(record["price"]) if record else None
