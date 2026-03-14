import uuid

from app.integrations.calendar.base import CalendarEventInput, CalendarEventResult, CalendarProvider


class GoogleCalendarProvider(CalendarProvider):
    def connect(self, auth_code: str | None, redirect_uri: str | None) -> dict:
        return {
            "provider": "google",
            "connected": True,
            "auth_code_received": bool(auth_code),
            "redirect_uri": redirect_uri,
        }

    def create_event(self, payload: CalendarEventInput) -> CalendarEventResult:
        return CalendarEventResult(external_event_id=f"gcal-{uuid.uuid4()}", status="scheduled")
