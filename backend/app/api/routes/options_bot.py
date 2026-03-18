from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.options_bot import (
    ETradeDataResponse,
    ETradeOptionChainRequest,
    ETradeOrderPayloadBuildRequest,
    ETradeOrderRequest,
    ETradeStatusResponse,
    OptionsBacktestRequest,
    OptionsBacktestResponse,
    OptionsSignalRequest,
    OptionsSignalResponse,
)
from app.services.etrade import ETradeAPIError, ETradeClient, ETradeConfigurationError, build_option_order_payload
from app.services.options_bot import (
    PriceBar,
    RiskConfig,
    StrategyConfig,
    generate_signal,
    run_backtest,
)

router = APIRouter(prefix="/options-bot", tags=["options-bot"])


def _as_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ETradeConfigurationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, ETradeAPIError):
        return HTTPException(
            status_code=502 if exc.status_code >= 500 else exc.status_code,
            detail={"message": exc.message, "provider_payload": exc.payload},
        )
    return HTTPException(status_code=500, detail=str(exc))


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
        metrics=asdict(result.metrics),
        trades=[asdict(item) for item in result.trades],
        equity_curve=[asdict(item) for item in result.equity_curve],
    )


@router.get("/etrade/status", response_model=ETradeStatusResponse)
def etrade_status():
    client = ETradeClient()
    return ETradeStatusResponse(
        configured=client.configured,
        sandbox=bool(settings.etrade_sandbox),
        base_url=client.base_url,
        has_account_id_key=bool(settings.etrade_account_id_key.strip()),
    )


@router.get("/etrade/accounts", response_model=ETradeDataResponse)
def etrade_accounts():
    client = ETradeClient()
    try:
        accounts = client.list_accounts()
    except Exception as exc:
        raise _as_http_error(exc) from exc
    return ETradeDataResponse(message="Accounts fetched from E*Trade.", data=accounts)


@router.post("/etrade/option-chain", response_model=ETradeDataResponse)
def etrade_option_chain(payload: ETradeOptionChainRequest):
    client = ETradeClient()
    try:
        chain = client.get_option_chain(
            symbol=payload.symbol,
            expiry_year=payload.expiry_year,
            expiry_month=payload.expiry_month,
            expiry_day=payload.expiry_day,
            strike_price_near=payload.strike_price_near,
            chain_type=payload.chain_type,
            skip_adjusted=payload.skip_adjusted,
            include_weeklys=payload.include_weeklys,
        )
    except Exception as exc:
        raise _as_http_error(exc) from exc
    return ETradeDataResponse(message="Option chain fetched from E*Trade.", data=chain)


@router.post("/etrade/order/payload", response_model=ETradeDataResponse)
def etrade_order_payload(payload: ETradeOrderPayloadBuildRequest):
    try:
        order_payload = build_option_order_payload(
            symbol=payload.symbol,
            call_put=payload.call_put,
            order_action=payload.order_action,
            quantity=payload.quantity,
            strike_price=payload.strike_price,
            expiry_year=payload.expiry_year,
            expiry_month=payload.expiry_month,
            expiry_day=payload.expiry_day,
            limit_price=payload.limit_price,
            client_order_id=payload.client_order_id,
            order_term=payload.order_term,
            market_session=payload.market_session,
            quantity_type=payload.quantity_type,
            all_or_none=payload.all_or_none,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ETradeDataResponse(message="Generated E*Trade-compatible options order payload.", data=order_payload)


@router.post("/etrade/order/preview", response_model=ETradeDataResponse)
def etrade_order_preview(payload: ETradeOrderRequest):
    client = ETradeClient()
    try:
        account_id_key = client.resolve_account_id_key(payload.account_id_key)
        preview_response = client.preview_order(account_id_key=account_id_key, payload=payload.payload)
    except Exception as exc:
        raise _as_http_error(exc) from exc
    return ETradeDataResponse(message="Preview order submitted to E*Trade.", data=preview_response)


@router.post("/etrade/order/place", response_model=ETradeDataResponse)
def etrade_order_place(payload: ETradeOrderRequest):
    client = ETradeClient()
    try:
        account_id_key = client.resolve_account_id_key(payload.account_id_key)
        place_response = client.place_order(account_id_key=account_id_key, payload=payload.payload)
    except Exception as exc:
        raise _as_http_error(exc) from exc
    return ETradeDataResponse(message="Live order submitted to E*Trade.", data=place_response)
