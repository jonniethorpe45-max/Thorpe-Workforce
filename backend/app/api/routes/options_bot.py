from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.schemas.options_bot import (
    ETradeConnectCompleteRequest,
    ETradeConnectStartRequest,
    ETradeConnectStartResponse,
    ETradeDataResponse,
    ETradeDisconnectResponse,
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
from app.services.etrade_credentials import (
    begin_workspace_oauth,
    complete_workspace_oauth,
    disconnect_workspace_account,
    get_pending_request_secret,
    get_workspace_tokens,
)
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


def _build_workspace_etrade_client(db: Session, current_user: User) -> tuple[ETradeClient, str, bool]:
    workspace_tokens = get_workspace_tokens(db, workspace_id=current_user.workspace_id)
    if workspace_tokens:
        access_token, access_token_secret, metadata = workspace_tokens
        account_id_key = str(metadata.get("account_id_key") or "")
        client = ETradeClient(
            access_token=access_token,
            access_token_secret=access_token_secret,
            account_id_key=account_id_key,
        )
        return client, "workspace", True

    fallback_client = ETradeClient()
    if fallback_client.configured:
        return fallback_client, "settings", False
    return fallback_client, "none", False


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
def etrade_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client, source, workspace_connected = _build_workspace_etrade_client(db, current_user)
    return ETradeStatusResponse(
        configured=client.configured,
        sandbox=bool(client.base_url.endswith("apisb.etrade.com")),
        base_url=client.base_url,
        has_account_id_key=bool(client.default_account_id_key),
        workspace_connected=workspace_connected,
        connection_source=source,
    )


@router.post("/etrade/connect/start", response_model=ETradeConnectStartResponse)
def etrade_connect_start(
    payload: ETradeConnectStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = ETradeClient()
    callback_url = (payload.redirect_uri or "").strip() or settings.etrade_oauth_callback_url
    try:
        request_token = client.request_token(callback_url=callback_url)
        begin_workspace_oauth(
            db,
            workspace_id=current_user.workspace_id,
            request_token=request_token["oauth_token"],
            request_token_secret=request_token["oauth_token_secret"],
            redirect_uri=callback_url,
            account_id_key=payload.account_id_key,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise _as_http_error(exc) from exc
    return ETradeConnectStartResponse(
        message="Open authorize_url in E*Trade, then call /options-bot/etrade/connect/complete with oauth_token and oauth_verifier.",
        oauth_token=request_token["oauth_token"],
        authorize_url=client.build_authorize_url(oauth_token=request_token["oauth_token"]),
        redirect_uri=callback_url,
    )


@router.post("/etrade/connect/complete", response_model=ETradeDataResponse)
def etrade_connect_complete(
    payload: ETradeConnectCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = ETradeClient()
    try:
        request_token_secret, metadata = get_pending_request_secret(
            db,
            workspace_id=current_user.workspace_id,
            oauth_token=payload.oauth_token,
        )
        access = client.exchange_access_token(
            oauth_token=payload.oauth_token,
            oauth_token_secret=request_token_secret,
            oauth_verifier=payload.oauth_verifier,
        )
        complete_workspace_oauth(
            db,
            workspace_id=current_user.workspace_id,
            expected_request_token=payload.oauth_token,
            access_token=access["access_token"],
            access_token_secret=access["access_token_secret"],
            account_id_key=payload.account_id_key or str(metadata.get("account_id_key") or ""),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise _as_http_error(exc) from exc
    return ETradeDataResponse(message="E*Trade OAuth connection completed for workspace.", data={"connected": True})


@router.delete("/etrade/connect", response_model=ETradeDisconnectResponse)
def etrade_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    disconnected = disconnect_workspace_account(db, workspace_id=current_user.workspace_id)
    db.commit()
    return ETradeDisconnectResponse(
        disconnected=disconnected,
        message="E*Trade workspace credentials removed." if disconnected else "No E*Trade workspace credentials were stored.",
    )


@router.get("/etrade/accounts", response_model=ETradeDataResponse)
def etrade_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client, _, _ = _build_workspace_etrade_client(db, current_user)
    try:
        accounts = client.list_accounts()
    except Exception as exc:
        raise _as_http_error(exc) from exc
    return ETradeDataResponse(message="Accounts fetched from E*Trade.", data=accounts)


@router.post("/etrade/option-chain", response_model=ETradeDataResponse)
def etrade_option_chain(
    payload: ETradeOptionChainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client, _, _ = _build_workspace_etrade_client(db, current_user)
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
def etrade_order_preview(
    payload: ETradeOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client, _, _ = _build_workspace_etrade_client(db, current_user)
    try:
        account_id_key = client.resolve_account_id_key(payload.account_id_key)
        preview_response = client.preview_order(account_id_key=account_id_key, payload=payload.payload)
    except Exception as exc:
        raise _as_http_error(exc) from exc
    return ETradeDataResponse(message="Preview order submitted to E*Trade.", data=preview_response)


@router.post("/etrade/order/place", response_model=ETradeDataResponse)
def etrade_order_place(
    payload: ETradeOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client, _, _ = _build_workspace_etrade_client(db, current_user)
    try:
        account_id_key = client.resolve_account_id_key(payload.account_id_key)
        place_response = client.place_order(account_id_key=account_id_key, payload=payload.payload)
    except Exception as exc:
        raise _as_http_error(exc) from exc
    return ETradeDataResponse(message="Live order submitted to E*Trade.", data=place_response)
