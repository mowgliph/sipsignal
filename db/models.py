"""
Modelos de base de datos para SipSignal.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class SignalBase(BaseModel):
    direction: str = Field(..., pattern="^(LONG|SHORT)$")
    entry_price: Optional[Decimal] = None
    tp1_level: Optional[Decimal] = None
    sl_level: Optional[Decimal] = None
    rr_ratio: Optional[Decimal] = None
    atr_value: Optional[Decimal] = None
    timeframe: str
    status: str = "EMITIDA"
    ai_context: Optional[str] = None


class SignalCreate(SignalBase):
    detected_at: datetime


class Signal(SignalBase):
    id: int
    detected_at: datetime
    taken_at: Optional[datetime] = None
    tp1_hit: bool = False
    tp1_hit_at: Optional[datetime] = None
    sl_moved_to_breakeven: bool = False
    close_price: Optional[Decimal] = None
    close_at: Optional[datetime] = None
    result: Optional[str] = None
    pnl_usdt: Optional[Decimal] = None
    pnl_percent: Optional[Decimal] = None
    supertrend_exit: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActiveTradeBase(BaseModel):
    signal_id: int
    direction: str = Field(..., pattern="^(LONG|SHORT)$")
    entry_price: Decimal
    tp1_level: Optional[Decimal] = None
    sl_level: Optional[Decimal] = None
    status: str = "ABIERTO"


class ActiveTradeCreate(ActiveTradeBase):
    pass


class ActiveTrade(ActiveTradeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserConfigBase(BaseModel):
    capital_total: Decimal = Field(default=Decimal("1000.00"))
    risk_percent: Decimal = Field(default=Decimal("1.00"))
    max_drawdown_percent: Decimal = Field(default=Decimal("5.00"))
    direction: str = Field(default="LONG", pattern="^(LONG|SHORT|AMBOS)$")
    timeframe_primary: str = Field(default="15m")
    setup_completed: bool = False


class UserConfigCreate(UserConfigBase):
    user_id: int


class UserConfig(UserConfigBase):
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class DrawdownTrackerBase(BaseModel):
    current_drawdown_usdt: Decimal = Field(default=Decimal("0.00"))
    current_drawdown_percent: Decimal = Field(default=Decimal("0.000"))
    losses_count: int = 0
    is_paused: bool = False


class DrawdownTrackerCreate(DrawdownTrackerBase):
    user_id: int


class DrawdownTracker(DrawdownTrackerBase):
    user_id: int
    last_reset_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True
