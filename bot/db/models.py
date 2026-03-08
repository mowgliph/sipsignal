"""
Modelos de base de datos para SipSignal.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SignalBase(BaseModel):
    direction: str = Field(..., pattern="^(LONG|SHORT)$")
    entry_price: Decimal | None = None
    tp1_level: Decimal | None = None
    sl_level: Decimal | None = None
    rr_ratio: Decimal | None = None
    atr_value: Decimal | None = None
    timeframe: str
    status: str = "EMITIDA"
    ai_context: str | None = None


class SignalCreate(SignalBase):
    detected_at: datetime


class Signal(SignalBase):
    id: int
    detected_at: datetime
    taken_at: datetime | None = None
    tp1_hit: bool = False
    tp1_hit_at: datetime | None = None
    sl_moved_to_breakeven: bool = False
    close_price: Decimal | None = None
    close_at: datetime | None = None
    result: str | None = None
    pnl_usdt: Decimal | None = None
    pnl_percent: Decimal | None = None
    supertrend_exit: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActiveTradeBase(BaseModel):
    signal_id: int
    direction: str = Field(..., pattern="^(LONG|SHORT)$")
    entry_price: Decimal
    tp1_level: Decimal | None = None
    sl_level: Decimal | None = None
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
    last_reset_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


class SignalModel(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    direction = Column(String(5), nullable=False)
    entry_price = Column(Numeric(12, 2))
    tp1_level = Column(Numeric(12, 2))
    sl_level = Column(Numeric(12, 2))
    rr_ratio = Column(Numeric(5, 3))
    atr_value = Column(Numeric(12, 2))
    timeframe = Column(String(5), nullable=False)
    status = Column(String(20), default="EMITIDA")
    taken_at = Column(DateTime(timezone=True))
    tp1_hit = Column(Boolean, default=False)
    tp1_hit_at = Column(DateTime(timezone=True))
    sl_moved_to_breakeven = Column(Boolean, default=False)
    close_price = Column(Numeric(12, 2))
    close_at = Column(DateTime(timezone=True))
    result = Column(String(15))
    pnl_usdt = Column(Numeric(10, 2))
    pnl_percent = Column(Numeric(6, 3))
    supertrend_exit = Column(Boolean, default=False)
    ai_context = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default="NOW()")
    updated_at = Column(DateTime(timezone=True), server_default="NOW()")

    __table_args__ = (
        CheckConstraint("direction IN ('LONG', 'SHORT')", name="signals_direction_check"),
        CheckConstraint(
            "status IN ('EMITIDA', 'TOMADA', 'CERRADA', 'CANCELADA')", name="signals_status_check"
        ),
    )


class ActiveTradeModel(Base):
    __tablename__ = "active_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    direction = Column(String(5), nullable=False)
    entry_price = Column(Numeric(12, 2), nullable=False)
    tp1_level = Column(Numeric(12, 2))
    sl_level = Column(Numeric(12, 2))
    status = Column(String(20), default="ABIERTO")
    created_at = Column(DateTime(timezone=True), server_default="NOW()")
    updated_at = Column(DateTime(timezone=True), server_default="NOW()")

    __table_args__ = (
        CheckConstraint("direction IN ('LONG', 'SHORT')", name="active_trades_direction_check"),
        CheckConstraint(
            "status IN ('ABIERTO', 'CERRADO', 'PAUSADO')", name="active_trades_status_check"
        ),
    )


class UserConfigModel(Base):
    __tablename__ = "user_config"

    user_id = Column(Integer, primary_key=True)
    capital_total = Column(Numeric(12, 2), default=1000.00)
    risk_percent = Column(Numeric(4, 2), default=1.00)
    max_drawdown_percent = Column(Numeric(4, 2), default=5.00)
    direction = Column(String(10), default="LONG")
    timeframe_primary = Column(String(5), default="15m")
    setup_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), server_default="NOW()")

    __table_args__ = (
        CheckConstraint(
            "direction IN ('LONG', 'SHORT', 'AMBOS')", name="user_config_direction_check"
        ),
    )


class DrawdownTrackerModel(Base):
    __tablename__ = "drawdown_tracker"

    user_id = Column(
        Integer, ForeignKey("user_config.user_id", ondelete="CASCADE"), primary_key=True
    )
    current_drawdown_usdt = Column(Numeric(10, 2), default=0.00)
    current_drawdown_percent = Column(Numeric(5, 3), default=0.000)
    losses_count = Column(Integer, default=0)
    last_reset_at = Column(DateTime(timezone=True))
    is_paused = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), server_default="NOW()")


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    language = Column(String(5), default="es")
    registered_at = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    status = Column(String(20), nullable=False, default="non_permitted")
    requested_at = Column(DateTime(timezone=True), nullable=True)
