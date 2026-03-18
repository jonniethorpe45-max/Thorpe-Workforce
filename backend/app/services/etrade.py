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
    def __init__(
        self,
        *,
        access_token: str | None = None,
        access_token_secret: str | None = None,
        account_id_key: str | None = None,
    ):
        self.consumer_key = settings.etrade_consumer_key.strip()
        self.consumer_secret = settings.etrade_consumer_secret.strip()
        self.access_token = (access_token or settings.etrade_access_token).strip()
        self.access_token_secret = (access_token_secret or settings.etrade_access_token_secret).strip()
        self.default_account_id_key = (account_id_key or settings.etrade_account_id_key).strip()
        self.request_timeout_seconds = max(2.0, float(settings.etrade_request_timeout_seconds))

        if settings.etrade_base_url_override.strip():
            self.base_url = settings.etrade_base_url_override.strip().rstrip("/")
        else:
            self.base_url = "https://apisb.etrade.com" if settings.etrade_sandbox else "https://api.etrade.com"
        self.authorize_base_url = "https://us.etrade.com"

    @property
    def configured(self) -> bool:
        return bool(self.consumer_key and self.consumer_secret and self.access_token and self.access_token_secret)

    @property
    def oauth_ready(self) -> bool:
        return bool(self.consumer_key and self.consumer_secret)

    def _ensure_configured(self, *, require_access_token: bool = True) -> None:
        if require_access_token and self.configured:
            return
        if not require_access_token and self.oauth_ready:
            return
        if not require_access_token:
            raise ETradeConfigurationError(
                "E*Trade OAuth app credentials are not configured. Set ETRADE_CONSUMER_KEY and ETRADE_CONSUMER_SECRET."
            )
        raise ETradeConfigurationError(
            "E*Trade credentials are not configured. Set ETRADE_CONSUMER_KEY, ETRADE_CONSUMER_SECRET, "
            "ETRADE_ACCESS_TOKEN, and ETRADE_ACCESS_TOKEN_SECRET."
        )

    def _session(
        self,
        *,
        resource_owner_key: str | None = None,
        resource_owner_secret: str | None = None,
        callback_uri: str | None = None,
        verifier: str | None = None,
        require_access_token: bool = True,
    ) -> OAuth1Session:
        self._ensure_configured(require_access_token=require_access_token)
        kwargs: dict[str, Any] = {
            "client_key": self.consumer_key,
            "client_secret": self.consumer_secret,
            "signature_method": "HMAC-SHA1",
        }
        if callback_uri:
            kwargs["callback_uri"] = callback_uri
        if verifier:
            kwargs["verifier"] = verifier
        owner_key = resource_owner_key if resource_owner_key is not None else self.access_token
        owner_secret = resource_owner_secret if resource_owner_secret is not None else self.access_token_secret
        if owner_key:
            kwargs["resource_owner_key"] = owner_key
        if owner_secret:
            kwargs["resource_owner_secret"] = owner_secret
        return OAuth1Session(**kwargs)

    def request_token(self, *, callback_url: str) -> dict[str, str]:
        session = self._session(callback_uri=callback_url, require_access_token=False)
        try:
            token = session.fetch_request_token(f"{self.base_url}/oauth/request_token")
        except requests.RequestException as exc:
            raise ETradeAPIError(status_code=502, message=f"E*Trade request token failed: {exc}") from exc
        oauth_token = str(token.get("oauth_token", "")).strip()
        oauth_token_secret = str(token.get("oauth_token_secret", "")).strip()
        if not oauth_token or not oauth_token_secret:
            raise ETradeAPIError(
                status_code=502,
                message="E*Trade request token response was missing token values.",
                payload=token,
            )
        return {"oauth_token": oauth_token, "oauth_token_secret": oauth_token_secret}

    def build_authorize_url(self, *, oauth_token: str) -> str:
        return f"{self.authorize_base_url}/e/t/etws/authorize?key={self.consumer_key}&token={oauth_token}"

    def exchange_access_token(
        self,
        *,
        oauth_token: str,
        oauth_token_secret: str,
        oauth_verifier: str,
    ) -> dict[str, str]:
        session = self._session(
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
            verifier=oauth_verifier,
            require_access_token=False,
        )
        try:
            token = session.fetch_access_token(f"{self.base_url}/oauth/access_token")
        except requests.RequestException as exc:
            raise ETradeAPIError(status_code=502, message=f"E*Trade access token exchange failed: {exc}") from exc
        access_token = str(token.get("oauth_token", "")).strip()
        access_token_secret = str(token.get("oauth_token_secret", "")).strip()
        if not access_token or not access_token_secret:
            raise ETradeAPIError(
                status_code=502,
                message="E*Trade access token response was missing token values.",
                payload=token,
            )
        return {"access_token": access_token, "access_token_secret": access_token_secret}

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self._session(require_access_token=True)
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
