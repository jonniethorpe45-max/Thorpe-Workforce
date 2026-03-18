from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import erf, exp, log, sqrt
from statistics import pstdev
from typing import Literal


SignalLabel = Literal["BULLISH", "BEARISH", "HOLD"]
OptionSide = Literal["call", "put"]


@dataclass(slots=True)
class PriceBar:
    close: float
    implied_vol: float = 0.35
    timestamp: datetime | None = None


@dataclass(slots=True)
class StrategyConfig:
    fast_window: int = 5
    slow_window: int = 20
    momentum_window: int = 5
    momentum_threshold: float = 0.015
    ma_buffer: float = 0.0
    days_to_expiry: int = 14
    max_holding_days: int = 7
    take_profit_pct: float = 0.45
    stop_loss_pct: float = 0.30


@dataclass(slots=True)
class RiskConfig:
    risk_per_trade_dollars: float = 400.0
    max_positions: int = 1
    max_contracts_per_trade: int = 3
    contract_fee: float = 1.0
    max_daily_loss_pct: float = 0.03
    max_drawdown_pct: float = 0.20
    min_cash_reserve: float = 1000.0
    min_days_to_expiry_exit: int = 2


@dataclass(slots=True)
class SignalSnapshot:
    signal: SignalLabel
    confidence: float
    rationale: str
    fast_ma: float | None
    slow_ma: float | None
    momentum: float | None


@dataclass(slots=True)
class EquityPoint:
    index: int
    timestamp: datetime | None
    equity: float


@dataclass(slots=True)
class ExecutedTrade:
    side: str
    entry_index: int
    exit_index: int
    entry_timestamp: datetime | None
    exit_timestamp: datetime | None
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


@dataclass(slots=True)
class BacktestMetrics:
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


@dataclass(slots=True)
class BacktestResult:
    message: str
    metrics: BacktestMetrics
    trades: list[ExecutedTrade]
    equity_curve: list[EquityPoint]


@dataclass(slots=True)
class _OpenPosition:
    side: OptionSide
    entry_index: int
    strike: float
    quantity: int
    entry_underlying: float
    entry_premium: float
    implied_vol: float
    days_to_expiry: int
    entry_timestamp: datetime | None
    entry_fee: float
    entry_cost: float


def _norm_cdf(value: float) -> float:
    return 0.5 * (1.0 + erf(value / sqrt(2.0)))


def _option_price(
    side: OptionSide,
    spot: float,
    strike: float,
    years_to_expiry: float,
    volatility: float,
    risk_free_rate: float,
) -> float:
    spot = max(spot, 0.01)
    strike = max(strike, 0.01)
    volatility = max(volatility, 0.0001)

    if years_to_expiry <= 0:
        intrinsic = max(0.0, spot - strike) if side == "call" else max(0.0, strike - spot)
        return intrinsic

    sqrt_t = sqrt(years_to_expiry)
    sigma_sqrt_t = volatility * sqrt_t
    d1 = (log(spot / strike) + (risk_free_rate + 0.5 * volatility * volatility) * years_to_expiry) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t

    if side == "call":
        return max(0.0, spot * _norm_cdf(d1) - strike * exp(-risk_free_rate * years_to_expiry) * _norm_cdf(d2))
    return max(0.0, strike * exp(-risk_free_rate * years_to_expiry) * _norm_cdf(-d2) - spot * _norm_cdf(-d1))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _rounded_strike(price: float, increment: int = 5) -> float:
    return float(round(price / increment) * increment)


def generate_signal(closes: list[float], config: StrategyConfig | None = None) -> SignalSnapshot:
    strategy = config or StrategyConfig()
    lookback = max(strategy.slow_window, strategy.momentum_window + 1)
    if len(closes) < lookback:
        return SignalSnapshot(
            signal="HOLD",
            confidence=0.0,
            rationale=f"Insufficient history. Need at least {lookback} closes.",
            fast_ma=None,
            slow_ma=None,
            momentum=None,
        )

    fast_ma = _mean(closes[-strategy.fast_window :])
    slow_ma = _mean(closes[-strategy.slow_window :])
    current_price = closes[-1]
    momentum_base = closes[-strategy.momentum_window - 1]
    momentum = (current_price / momentum_base) - 1.0 if momentum_base > 0 else 0.0

    bullish = fast_ma > slow_ma * (1.0 + strategy.ma_buffer) and momentum >= strategy.momentum_threshold
    bearish = fast_ma < slow_ma * (1.0 - strategy.ma_buffer) and momentum <= -strategy.momentum_threshold

    trend_strength = abs(fast_ma - slow_ma) / max(current_price, 0.01)
    momentum_strength = abs(momentum)
    confidence = min(1.0, (trend_strength * 20.0) + (momentum_strength * 10.0))

    if bullish:
        return SignalSnapshot(
            signal="BULLISH",
            confidence=confidence,
            rationale="Fast MA is above slow MA with positive momentum.",
            fast_ma=fast_ma,
            slow_ma=slow_ma,
            momentum=momentum,
        )
    if bearish:
        return SignalSnapshot(
            signal="BEARISH",
            confidence=confidence,
            rationale="Fast MA is below slow MA with negative momentum.",
            fast_ma=fast_ma,
            slow_ma=slow_ma,
            momentum=momentum,
        )
    return SignalSnapshot(
        signal="HOLD",
        confidence=max(0.05, confidence * 0.4),
        rationale="Trend and momentum are mixed; no clean directional edge.",
        fast_ma=fast_ma,
        slow_ma=slow_ma,
        momentum=momentum,
    )


def _mark_to_market_value(
    position: _OpenPosition,
    index: int,
    current_spot: float,
    risk_free_rate: float,
) -> float:
    elapsed = index - position.entry_index
    remaining_days = max(position.days_to_expiry - elapsed, 0)
    years_to_expiry = remaining_days / 252.0
    premium = _option_price(
        side=position.side,
        spot=current_spot,
        strike=position.strike,
        years_to_expiry=years_to_expiry,
        volatility=position.implied_vol,
        risk_free_rate=risk_free_rate,
    )
    return premium * 100.0 * position.quantity


def run_backtest(
    bars: list[PriceBar],
    strategy: StrategyConfig | None = None,
    risk: RiskConfig | None = None,
    *,
    starting_cash: float = 25_000.0,
    risk_free_rate: float = 0.03,
    assumed_slippage_pct: float = 0.01,
) -> BacktestResult:
    if not bars:
        raise ValueError("bars cannot be empty")

    strategy_cfg = strategy or StrategyConfig()
    risk_cfg = risk or RiskConfig()
    slippage = max(0.0, assumed_slippage_pct)

    cash = starting_cash
    open_positions: list[_OpenPosition] = []
    closed_trades: list[ExecutedTrade] = []
    equity_curve: list[EquityPoint] = []
    closes_history: list[float] = []

    day_start_equity = starting_cash
    current_day = bars[0].timestamp.date() if bars[0].timestamp else 0
    peak_equity = starting_cash
    max_drawdown = 0.0
    trading_halted = False

    def current_equity(index: int, current_spot: float) -> float:
        market_value = sum(_mark_to_market_value(position, index, current_spot, risk_free_rate) for position in open_positions)
        return cash + market_value

    def close_position(position: _OpenPosition, index: int, reason: str) -> None:
        nonlocal cash
        elapsed = index - position.entry_index
        remaining_days = max(position.days_to_expiry - elapsed, 0)
        years_to_expiry = remaining_days / 252.0
        bar = bars[index]
        exit_mid = _option_price(
            side=position.side,
            spot=bar.close,
            strike=position.strike,
            years_to_expiry=years_to_expiry,
            volatility=position.implied_vol,
            risk_free_rate=risk_free_rate,
        )
        exit_premium = max(0.01, exit_mid * (1.0 - slippage))
        exit_value = exit_premium * 100.0 * position.quantity
        exit_fee = risk_cfg.contract_fee * position.quantity
        cash += exit_value - exit_fee

        gross_pnl = (exit_premium - position.entry_premium) * 100.0 * position.quantity
        total_fees = position.entry_fee + exit_fee
        net_pnl = gross_pnl - total_fees
        basis = max(position.entry_premium * 100.0 * position.quantity, 1.0)
        pnl_pct = net_pnl / basis

        closed_trades.append(
            ExecutedTrade(
                side=position.side.upper(),
                entry_index=position.entry_index,
                exit_index=index,
                entry_timestamp=position.entry_timestamp,
                exit_timestamp=bar.timestamp,
                strike=position.strike,
                contracts=position.quantity,
                entry_underlying=position.entry_underlying,
                exit_underlying=bar.close,
                entry_premium=position.entry_premium,
                exit_premium=exit_premium,
                pnl=net_pnl,
                pnl_pct=pnl_pct,
                total_fees=total_fees,
                days_held=elapsed,
                exit_reason=reason,
            )
        )

    for index, bar in enumerate(bars):
        closes_history.append(bar.close)

        day_marker = bar.timestamp.date() if bar.timestamp else index
        if day_marker != current_day:
            current_day = day_marker
            day_start_equity = current_equity(index, bar.close)

        signal_snapshot = generate_signal(closes_history, strategy_cfg)

        remaining_open_positions: list[_OpenPosition] = []
        for position in open_positions:
            held_days = index - position.entry_index
            remaining_days = max(position.days_to_expiry - held_days, 0)
            position_value = _mark_to_market_value(position, index, bar.close, risk_free_rate)
            entry_value = max(position.entry_premium * 100.0 * position.quantity, 1.0)
            unrealized_pct = (position_value - entry_value) / entry_value

            should_exit = False
            reason = ""
            if unrealized_pct >= strategy_cfg.take_profit_pct:
                should_exit = True
                reason = "take_profit"
            elif unrealized_pct <= -strategy_cfg.stop_loss_pct:
                should_exit = True
                reason = "stop_loss"
            elif held_days >= strategy_cfg.max_holding_days:
                should_exit = True
                reason = "max_holding"
            elif remaining_days <= risk_cfg.min_days_to_expiry_exit:
                should_exit = True
                reason = "expiry_protection"
            elif position.side == "call" and signal_snapshot.signal == "BEARISH":
                should_exit = True
                reason = "signal_flip"
            elif position.side == "put" and signal_snapshot.signal == "BULLISH":
                should_exit = True
                reason = "signal_flip"

            if should_exit:
                close_position(position, index, reason)
            else:
                remaining_open_positions.append(position)
        open_positions = remaining_open_positions

        equity_now = current_equity(index, bar.close)
        peak_equity = max(peak_equity, equity_now)
        drawdown = (peak_equity - equity_now) / peak_equity if peak_equity > 0 else 0.0
        max_drawdown = max(max_drawdown, drawdown)
        equity_curve.append(EquityPoint(index=index, timestamp=bar.timestamp, equity=equity_now))

        if drawdown >= risk_cfg.max_drawdown_pct:
            for position in open_positions:
                close_position(position, index, "max_drawdown_guard")
            open_positions = []
            trading_halted = True
            break

        intraday_loss = (equity_now - day_start_equity) / day_start_equity if day_start_equity > 0 else 0.0
        daily_loss_block = intraday_loss <= -risk_cfg.max_daily_loss_pct

        if trading_halted:
            continue
        if signal_snapshot.signal == "HOLD":
            continue
        if daily_loss_block:
            continue
        if len(open_positions) >= risk_cfg.max_positions:
            continue

        side: OptionSide = "call" if signal_snapshot.signal == "BULLISH" else "put"
        strike = _rounded_strike(bar.close)
        entry_mid = _option_price(
            side=side,
            spot=bar.close,
            strike=strike,
            years_to_expiry=strategy_cfg.days_to_expiry / 252.0,
            volatility=bar.implied_vol,
            risk_free_rate=risk_free_rate,
        )
        entry_premium = max(0.01, entry_mid * (1.0 + slippage))
        premium_value_per_contract = entry_premium * 100.0
        entry_fee_per_contract = risk_cfg.contract_fee
        total_cost_per_contract = premium_value_per_contract + entry_fee_per_contract

        if total_cost_per_contract <= 0:
            continue

        risk_sized_contracts = int(risk_cfg.risk_per_trade_dollars // premium_value_per_contract)
        cash_available = max(0.0, cash - risk_cfg.min_cash_reserve)
        cash_sized_contracts = int(cash_available // total_cost_per_contract)
        quantity = min(risk_sized_contracts, cash_sized_contracts, risk_cfg.max_contracts_per_trade)
        if quantity < 1:
            continue

        entry_cost = premium_value_per_contract * quantity
        entry_fee = entry_fee_per_contract * quantity
        cash -= entry_cost + entry_fee
        open_positions.append(
            _OpenPosition(
                side=side,
                entry_index=index,
                strike=strike,
                quantity=quantity,
                entry_underlying=bar.close,
                entry_premium=entry_premium,
                implied_vol=bar.implied_vol,
                days_to_expiry=strategy_cfg.days_to_expiry,
                entry_timestamp=bar.timestamp,
                entry_fee=entry_fee,
                entry_cost=entry_cost,
            )
        )

    if open_positions:
        last_index = len(bars) - 1
        for position in open_positions:
            close_position(position, last_index, "end_of_backtest")
        final_spot = bars[last_index].close
        equity_curve.append(EquityPoint(index=last_index, timestamp=bars[last_index].timestamp, equity=current_equity(last_index, final_spot)))

    ending_equity = cash
    total_return = (ending_equity - starting_cash) / starting_cash if starting_cash > 0 else 0.0

    total_trades = len(closed_trades)
    winning_trades = sum(1 for trade in closed_trades if trade.pnl > 0)
    gross_profit = sum(trade.pnl for trade in closed_trades if trade.pnl > 0)
    gross_loss = abs(sum(trade.pnl for trade in closed_trades if trade.pnl < 0))
    net_profit = gross_profit - gross_loss
    win_rate = (winning_trades / total_trades) if total_trades else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)

    returns: list[float] = []
    for idx in range(1, len(equity_curve)):
        prev = equity_curve[idx - 1].equity
        curr = equity_curve[idx].equity
        if prev > 0:
            returns.append((curr / prev) - 1.0)
    if returns and pstdev(returns) > 0:
        sharpe_ratio = (_mean(returns) / pstdev(returns)) * sqrt(252.0)
    else:
        sharpe_ratio = 0.0

    metrics = BacktestMetrics(
        starting_cash=starting_cash,
        ending_equity=ending_equity,
        total_return_pct=total_return,
        max_drawdown_pct=max_drawdown,
        total_trades=total_trades,
        winning_trades=winning_trades,
        win_rate=win_rate,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=net_profit,
        profit_factor=profit_factor,
        sharpe_ratio=sharpe_ratio,
    )
    return BacktestResult(
        message=(
            "Backtest completed. This is a simulation only and cannot guarantee future profits."
            if not trading_halted
            else "Backtest halted by risk guard. This is a simulation only and cannot guarantee future profits."
        ),
        metrics=metrics,
        trades=closed_trades,
        equity_curve=equity_curve,
    )
