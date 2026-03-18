def _trend_regime_bars() -> list[dict]:
    bars: list[dict] = []
    price = 100.0
    for idx in range(120):
        if idx < 40:
            price += 0.9
        elif idx < 80:
            price -= 0.8
        else:
            price += 1.1
        bars.append({"close": round(price, 2), "implied_vol": 0.35})
    return bars


def test_options_signal_bullish(client):
    closes = [100 + value for value in range(30)]
    response = client.post("/options-bot/signal", json={"closes": closes})
    assert response.status_code == 200
    payload = response.json()
    assert payload["signal"] == "BULLISH"
    assert payload["confidence"] >= 0


def test_options_backtest_runs_and_returns_metrics(client):
    payload = {
        "bars": _trend_regime_bars(),
        "starting_cash": 25000,
        "strategy": {
            "fast_window": 5,
            "slow_window": 20,
            "momentum_window": 5,
            "momentum_threshold": 0.01,
            "take_profit_pct": 0.35,
            "stop_loss_pct": 0.2,
            "days_to_expiry": 20,
            "max_holding_days": 10,
        },
        "risk": {
            "risk_per_trade_dollars": 500,
            "max_positions": 1,
            "max_contracts_per_trade": 2,
            "max_drawdown_pct": 0.30,
            "max_daily_loss_pct": 0.08,
        },
    }
    response = client.post("/options-bot/backtest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "simulation only" in data["message"].lower()
    assert data["metrics"]["total_trades"] > 0
    assert data["metrics"]["ending_equity"] > 0
    assert len(data["equity_curve"]) >= len(payload["bars"])


def test_options_backtest_rejects_short_history(client):
    bars = [{"close": 100 + idx, "implied_vol": 0.25} for idx in range(20)]
    response = client.post("/options-bot/backtest", json={"bars": bars})
    assert response.status_code == 422


def test_etrade_status_reflects_configuration_state(client, auth_headers):
    response = client.get("/options-bot/etrade/status", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "etrade"
    assert payload["configured"] is False
    assert payload["workspace_connected"] is False
    assert payload["connection_source"] == "none"


def test_etrade_order_payload_builder(client):
    response = client.post(
        "/options-bot/etrade/order/payload",
        json={
            "symbol": "aapl",
            "call_put": "CALL",
            "order_action": "BUY_OPEN",
            "quantity": 1,
            "strike_price": 200,
            "expiry_year": 2026,
            "expiry_month": 6,
            "expiry_day": 19,
            "limit_price": 4.25,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    instrument = data["PreviewOrderRequest"]["Order"][0]["Instrument"][0]
    assert instrument["Product"]["symbol"] == "AAPL"
    assert instrument["Product"]["callPut"] == "CALL"
    assert instrument["orderAction"] == "BUY_OPEN"


def test_etrade_accounts_uses_provider(client, auth_headers, monkeypatch):
    from app.api.routes import options_bot as options_bot_route

    class _FakeETradeClient:
        configured = True
        base_url = "https://apisb.etrade.com"
        default_account_id_key = "ABC123KEY"

        def list_accounts(self):
            return [{"accountId": "12345678", "accountIdKey": "ABC123KEY"}]

    monkeypatch.setattr(
        options_bot_route,
        "_build_workspace_etrade_client",
        lambda db, current_user: (_FakeETradeClient(), "workspace", True),
    )
    response = client.get("/options-bot/etrade/accounts", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "etrade"
    assert payload["data"][0]["accountIdKey"] == "ABC123KEY"


def test_etrade_preview_requires_configuration_or_account_key(client, auth_headers):
    response = client.post(
        "/options-bot/etrade/order/preview",
        headers=auth_headers,
        json={"payload": {"PreviewOrderRequest": {}}},
    )
    assert response.status_code == 400


def test_etrade_oauth_connect_flow_persists_workspace_connection(client, auth_headers, monkeypatch):
    from app.api.routes import options_bot as options_bot_route

    class _FakeETradeClient:
        configured = True
        base_url = "https://apisb.etrade.com"
        default_account_id_key = ""

        def __init__(self, *args, **kwargs):
            pass

        def request_token(self, *, callback_url: str):
            return {"oauth_token": "req_token_123", "oauth_token_secret": "req_secret_123"}

        def build_authorize_url(self, *, oauth_token: str):
            return f"https://example.com/auth?token={oauth_token}"

        def exchange_access_token(self, *, oauth_token: str, oauth_token_secret: str, oauth_verifier: str):
            assert oauth_token == "req_token_123"
            assert oauth_token_secret == "req_secret_123"
            assert oauth_verifier == "verifier_abc"
            return {"access_token": "access_789", "access_token_secret": "access_secret_789"}

    monkeypatch.setattr(options_bot_route, "ETradeClient", _FakeETradeClient)

    start = client.post(
        "/options-bot/etrade/connect/start",
        headers=auth_headers,
        json={"redirect_uri": "http://localhost/callback", "account_id_key": "WS_ACC_1"},
    )
    assert start.status_code == 200
    start_payload = start.json()
    assert start_payload["oauth_token"] == "req_token_123"
    assert "authorize_url" in start_payload

    complete = client.post(
        "/options-bot/etrade/connect/complete",
        headers=auth_headers,
        json={"oauth_token": "req_token_123", "oauth_verifier": "verifier_abc"},
    )
    assert complete.status_code == 200
    assert complete.json()["data"]["connected"] is True

    disconnect = client.delete("/options-bot/etrade/connect", headers=auth_headers)
    assert disconnect.status_code == 200
    assert disconnect.json()["disconnected"] is True
