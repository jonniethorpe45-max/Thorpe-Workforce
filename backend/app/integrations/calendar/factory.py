from app.core.config import settings
from app.integrations.calendar.base import CalendarProvider
from app.integrations.calendar.google_provider import GoogleCalendarProvider
from app.integrations.calendar.mock_provider import MockCalendarProvider


def get_calendar_provider() -> CalendarProvider:
    if settings.calendar_provider == "google":
        return GoogleCalendarProvider()
    return MockCalendarProvider()
