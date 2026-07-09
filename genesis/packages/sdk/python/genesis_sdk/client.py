from __future__ import annotations

from typing import Any

import requests


class GenesisClient:
    """Gateway-first Python client for Project Genesis."""

    def __init__(self, gateway_url: str = "http://localhost:7999", user_id: str = "demo-user"):
        self.gateway_url = gateway_url.rstrip("/")
        self.user_id = user_id

    def _url(self, path: str) -> str:
        return f"{self.gateway_url}{path}"

    def intent(self, message: str, user_id: str | None = None) -> dict[str, Any]:
        response = requests.post(
            self._url("/gateway/intent"),
            json={"message": message, "user_id": user_id or self.user_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def approve(self, approval_id: str, approved_by: str | None = None) -> dict[str, Any]:
        response = requests.post(
            self._url("/gateway/approvals/approve"),
            json={"approval_id": approval_id, "approved_by": approved_by or self.user_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def execute(self, approval_id: str, executed_by: str | None = None) -> dict[str, Any]:
        response = requests.post(
            self._url("/gateway/execute"),
            json={"approval_id": approval_id, "executed_by": executed_by or self.user_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def audit(self) -> list[dict[str, Any]]:
        response = requests.get(self._url("/gateway/audit"), timeout=30)
        response.raise_for_status()
        return response.json()

    def approvals(self) -> list[dict[str, Any]]:
        response = requests.get(self._url("/gateway/approvals"), timeout=30)
        response.raise_for_status()
        return response.json()

    def services(self) -> list[dict[str, Any]]:
        response = requests.get(self._url("/gateway/services"), timeout=30)
        response.raise_for_status()
        return response.json()

    def capabilities(self) -> list[dict[str, Any]]:
        response = requests.get(self._url("/gateway/capabilities"), timeout=30)
        response.raise_for_status()
        return response.json()
