from __future__ import annotations

import uuid
from typing import Any, Literal

import requests
from requests_oauthlib import OAuth1Session

from app.core.config import settings


OrderAction = Literal[
    "BUY_OPEN",
    "SELL_OPEN",
    "BUY_CLOSE",
    "SELL_CLOSE",
]
CallPut = Literal["CALL", "PUT"]


class ETradeConfigurationError(Exception):
    pass


class ETradeAPIError(Exception):
    def __init__(self, status_code: int, message: str, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.payload = payload or {}


class ETradeClient:
    def __init__(self):
        self.consumer_key = settings.etrade_consumer_key.strip()
        self.consumer_secret = settings.etrade_consumer_secret.strip()
        self.access_token = settings.etrade_access_token.strip()
        self.access_token_secret = settings.etrade_access_token_secret.strip()
        self.default_account_id_key = settings.etrade_account_id_key.strip()
        self.request_timeout_seconds = max(2.0, float(settings.etrade_request_timeout_seconds))

        if settings.etrade_base_url_override.strip():
            self.base_url = settings.etrade_base_url_override.strip().rstrip("/")
        else:
            self.base_url = "https://apisb.etrade.com" if settings.etrade_sandbox else "https://api.etrade.com"

    @property
    def configured(self) -> bool:
        return bool(self.consumer_key and self.consumer_secret and self.access_token and self.access_token_secret)

    def _ensure_configured(self) -> None:
        if self.configured:
            return
        raise ETradeConfigurationError(
            "E*Trade credentials are not configured. Set ETRADE_CONSUMER_KEY, ETRADE_CONSUMER_SECRET, "
            "ETRADE_ACCESS_TOKEN, and ETRADE_ACCESS_TOKEN_SECRET."
        )

    def _session(self) -> OAuth1Session:
        self._ensure_configured()
        return OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
            signature_method="HMAC-SHA1",
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self._session()
        url = f"{self.base_url}{path}"
        try:
            response = session.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                headers={"Accept": "application/json"},
                timeout=self.request_timeout_seconds,
            )
        except requests.RequestException as exc:
            raise ETradeAPIError(status_code=502, message=f"E*Trade request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_response": response.text}

        if response.status_code >= 400:
            message = payload.get("Error", {}).get("message") if isinstance(payload, dict) else None
            raise ETradeAPIError(
                status_code=response.status_code,
                message=message or f"E*Trade API returned HTTP {response.status_code}",
                payload=payload if isinstance(payload, dict) else {"response": payload},
            )
        if isinstance(payload, dict):
            return payload
        return {"response": payload}

    def resolve_account_id_key(self, account_id_key: str | None = None) -> str:
        resolved = (account_id_key or self.default_account_id_key).strip()
        if resolved:
            return resolved
        raise ETradeConfigurationError("No E*Trade account_id_key provided. Set ETRADE_ACCOUNT_ID_KEY or pass one in request.")

    def list_accounts(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/v1/accounts/list.json")
        accounts = payload.get("AccountListResponse", {}).get("Accounts", {}).get("Account", [])
        if isinstance(accounts, dict):
            return [accounts]
        if isinstance(accounts, list):
            return accounts
        return []

    def get_option_chain(
        self,
        *,
        symbol: str,
        expiry_year: int | None = None,
        expiry_month: int | None = None,
        expiry_day: int | None = None,
        strike_price_near: float | None = None,
        chain_type: str | None = None,
        skip_adjusted: bool = True,
        include_weeklys: bool = True,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"symbol": symbol.upper()}
        if expiry_year is not None:
            params["expiryYear"] = expiry_year
        if expiry_month is not None:
            params["expiryMonth"] = expiry_month
        if expiry_day is not None:
            params["expiryDay"] = expiry_day
        if strike_price_near is not None:
            params["strikePriceNear"] = strike_price_near
        if chain_type is not None:
            params["chainType"] = chain_type.upper()
        params["skipAdjusted"] = str(skip_adjusted).lower()
        params["includeWeekly"] = str(include_weeklys).lower()
        return self._request("GET", "/v1/market/optionchains.json", params=params)

    def preview_order(self, *, account_id_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = f"/v1/accounts/{account_id_key}/orders/preview.json"
        return self._request("POST", path, json_body=payload)

    def place_order(self, *, account_id_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = f"/v1/accounts/{account_id_key}/orders/place.json"
        return self._request("POST", path, json_body=payload)


def build_option_order_payload(
    *,
    symbol: str,
    call_put: CallPut,
    order_action: OrderAction,
    quantity: int,
    strike_price: float,
    expiry_year: int,
    expiry_month: int,
    expiry_day: int,
    limit_price: float,
    client_order_id: str | None = None,
    order_term: str = "GOOD_FOR_DAY",
    market_session: str = "REGULAR",
    quantity_type: str = "QUANTITY",
    all_or_none: bool = False,
) -> dict[str, Any]:
    if quantity < 1:
        raise ValueError("quantity must be >= 1")
    if limit_price <= 0:
        raise ValueError("limit_price must be > 0")
    if strike_price <= 0:
        raise ValueError("strike_price must be > 0")

    return {
        "PreviewOrderRequest": {
            "orderType": "OPTN",
            "clientOrderId": client_order_id or str(uuid.uuid4()),
            "Order": [
                {
                    "allOrNone": all_or_none,
                    "priceType": "LIMIT",
                    "orderTerm": order_term,
                    "marketSession": market_session,
                    "limitPrice": float(limit_price),
                    "Instrument": [
                        {
                            "Product": {
                                "securityType": "OPTN",
                                "symbol": symbol.upper(),
                                "expiryYear": expiry_year,
                                "expiryMonth": expiry_month,
                                "expiryDay": expiry_day,
                                "strikePrice": float(strike_price),
                                "callPut": call_put,
                            },
                            "orderAction": order_action,
                            "quantityType": quantity_type,
                            "quantity": quantity,
                        }
                    ],
                }
            ],
        }
    }
