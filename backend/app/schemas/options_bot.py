from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class OptionsBarInput(BaseModel):
    timestamp: datetime | None = None
    close: float = Field(gt=0)
    implied_vol: float = Field(default=0.35, gt=0.01, le=4.0)


class OptionsStrategyConfigInput(BaseModel):
    fast_window: int = Field(default=5, ge=2, le=100)
    slow_window: int = Field(default=20, ge=3, le=300)
    momentum_window: int = Field(default=5, ge=1, le=100)
    momentum_threshold: float = Field(default=0.015, ge=0.0, le=1.0)
    ma_buffer: float = Field(default=0.0, ge=0.0, le=0.20)
    days_to_expiry: int = Field(default=14, ge=3, le=90)
    max_holding_days: int = Field(default=7, ge=1, le=60)
    take_profit_pct: float = Field(default=0.45, gt=0.0, le=5.0)
    stop_loss_pct: float = Field(default=0.30, gt=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_relationships(self):
        if self.fast_window >= self.slow_window:
            raise ValueError("fast_window must be lower than slow_window")
        if self.max_holding_days > self.days_to_expiry:
            raise ValueError("max_holding_days cannot exceed days_to_expiry")
        return self


class OptionsRiskConfigInput(BaseModel):
    risk_per_trade_dollars: float = Field(default=400.0, gt=10, le=100000)
    max_positions: int = Field(default=1, ge=1, le=10)
    max_contracts_per_trade: int = Field(default=3, ge=1, le=100)
    contract_fee: float = Field(default=1.0, ge=0.0, le=25.0)
    max_daily_loss_pct: float = Field(default=0.03, gt=0.0, le=0.50)
    max_drawdown_pct: float = Field(default=0.20, gt=0.01, le=0.90)
    min_cash_reserve: float = Field(default=1000.0, ge=0.0)
    min_days_to_expiry_exit: int = Field(default=2, ge=0, le=30)


class OptionsSignalRequest(BaseModel):
    closes: list[float] = Field(min_length=10, max_length=1500)
    strategy: OptionsStrategyConfigInput = Field(default_factory=OptionsStrategyConfigInput)

    @model_validator(mode="after")
    def validate_closes(self):
        if any(value <= 0 for value in self.closes):
            raise ValueError("All closes must be > 0")
        return self


class OptionsSignalResponse(BaseModel):
    signal: Literal["BULLISH", "BEARISH", "HOLD"]
    confidence: float
    rationale: str
    fast_ma: float | None = None
    slow_ma: float | None = None
    momentum: float | None = None


class OptionsBacktestRequest(BaseModel):
    bars: list[OptionsBarInput] = Field(min_length=30, max_length=5000)
    starting_cash: float = Field(default=25000.0, gt=1000, le=1_000_000)
    risk_free_rate: float = Field(default=0.03, ge=0.0, le=0.20)
    assumed_slippage_pct: float = Field(default=0.01, ge=0.0, le=0.10)
    strategy: OptionsStrategyConfigInput = Field(default_factory=OptionsStrategyConfigInput)
    risk: OptionsRiskConfigInput = Field(default_factory=OptionsRiskConfigInput)

    @model_validator(mode="after")
    def validate_bars_count(self):
        if len(self.bars) < self.strategy.slow_window + 2:
            raise ValueError("bars length must be at least slow_window + 2")
        return self


class OptionsTradeRead(BaseModel):
    side: Literal["CALL", "PUT"]
    entry_index: int
    exit_index: int
    entry_timestamp: datetime | None = None
    exit_timestamp: datetime | None = None
    strike: float
    contracts: int
    entry_underlying: float
    exit_underlying: float
    entry_premium: float
    exit_premium: float
    pnl: float
    pnl_pct: float
    total_fees: float
    days_held: int
    exit_reason: str


class OptionsEquityPointRead(BaseModel):
    index: int
    timestamp: datetime | None = None
    equity: float


class OptionsBacktestMetricsRead(BaseModel):
    starting_cash: float
    ending_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    win_rate: float
    gross_profit: float
    gross_loss: float
    net_profit: float
    profit_factor: float
    sharpe_ratio: float


class OptionsBacktestResponse(BaseModel):
    message: str
    metrics: OptionsBacktestMetricsRead
    trades: list[OptionsTradeRead]
    equity_curve: list[OptionsEquityPointRead]


class ETradeStatusResponse(BaseModel):
    provider: str = "etrade"
    configured: bool
    sandbox: bool
    base_url: str
    has_account_id_key: bool
    workspace_connected: bool = False
    connection_source: Literal["workspace", "settings", "none"] = "none"


class ETradeDataResponse(BaseModel):
    provider: str = "etrade"
    message: str
    data: dict[str, Any] | list[dict[str, Any]]


class ETradeOptionChainRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=15)
    expiry_year: int | None = Field(default=None, ge=2000, le=2100)
    expiry_month: int | None = Field(default=None, ge=1, le=12)
    expiry_day: int | None = Field(default=None, ge=1, le=31)
    strike_price_near: float | None = Field(default=None, gt=0)
    chain_type: Literal["CALL", "PUT", "CALLPUT"] | None = None
    skip_adjusted: bool = True
    include_weeklys: bool = True

    @model_validator(mode="after")
    def normalize_symbol(self):
        self.symbol = self.symbol.strip().upper()
        return self


class ETradeOrderPayloadBuildRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=15)
    call_put: Literal["CALL", "PUT"]
    order_action: Literal["BUY_OPEN", "SELL_OPEN", "BUY_CLOSE", "SELL_CLOSE"]
    quantity: int = Field(ge=1, le=1000)
    strike_price: float = Field(gt=0)
    expiry_year: int = Field(ge=2000, le=2100)
    expiry_month: int = Field(ge=1, le=12)
    expiry_day: int = Field(ge=1, le=31)
    limit_price: float = Field(gt=0)
    client_order_id: str | None = Field(default=None, max_length=120)
    order_term: str = Field(default="GOOD_FOR_DAY", min_length=2, max_length=60)
    market_session: str = Field(default="REGULAR", min_length=2, max_length=60)
    quantity_type: str = Field(default="QUANTITY", min_length=2, max_length=60)
    all_or_none: bool = False

    @model_validator(mode="after")
    def normalize_symbol(self):
        self.symbol = self.symbol.strip().upper()
        return self


class ETradeOrderRequest(BaseModel):
    account_id_key: str | None = Field(default=None, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


class ETradeConnectStartRequest(BaseModel):
    redirect_uri: str | None = Field(default=None, max_length=2000)
    account_id_key: str | None = Field(default=None, max_length=120)


class ETradeConnectStartResponse(BaseModel):
    provider: str = "etrade"
    message: str
    oauth_token: str
    authorize_url: str
    redirect_uri: str


class ETradeConnectCompleteRequest(BaseModel):
    oauth_token: str = Field(min_length=5, max_length=255)
    oauth_verifier: str = Field(min_length=3, max_length=255)
    account_id_key: str | None = Field(default=None, max_length=120)


class ETradeDisconnectResponse(BaseModel):
    provider: str = "etrade"
    disconnected: bool = True
    message: str
