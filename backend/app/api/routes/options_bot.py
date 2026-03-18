from fastapi import APIRouter

from app.schemas.options_bot import (
    OptionsBacktestRequest,
    OptionsBacktestResponse,
    OptionsSignalRequest,
    OptionsSignalResponse,
)
from app.services.options_bot import (
    PriceBar,
    RiskConfig,
    StrategyConfig,
    generate_signal,
    run_backtest,
)

router = APIRouter(prefix="/options-bot", tags=["options-bot"])


@router.post("/signal", response_model=OptionsSignalResponse)
def options_signal(payload: OptionsSignalRequest):
    strategy = StrategyConfig(**payload.strategy.model_dump())
    snapshot = generate_signal(payload.closes, strategy)
    return OptionsSignalResponse(
        signal=snapshot.signal,
        confidence=snapshot.confidence,
        rationale=snapshot.rationale,
        fast_ma=snapshot.fast_ma,
        slow_ma=snapshot.slow_ma,
        momentum=snapshot.momentum,
    )


@router.post("/backtest", response_model=OptionsBacktestResponse)
def options_backtest(payload: OptionsBacktestRequest):
    strategy = StrategyConfig(**payload.strategy.model_dump())
    risk = RiskConfig(**payload.risk.model_dump())
    bars = [PriceBar(close=item.close, implied_vol=item.implied_vol, timestamp=item.timestamp) for item in payload.bars]

    result = run_backtest(
        bars=bars,
        strategy=strategy,
        risk=risk,
        starting_cash=payload.starting_cash,
        risk_free_rate=payload.risk_free_rate,
        assumed_slippage_pct=payload.assumed_slippage_pct,
    )
    return OptionsBacktestResponse(
        message=result.message,
        metrics=result.metrics,
        trades=result.trades,
        equity_curve=result.equity_curve,
    )
