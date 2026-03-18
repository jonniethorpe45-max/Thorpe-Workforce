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
