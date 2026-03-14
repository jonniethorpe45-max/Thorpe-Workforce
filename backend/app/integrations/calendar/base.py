from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CalendarEventInput:
    title: str
    start: datetime
    end: datetime
    attendee_email: str


@dataclass
class CalendarEventResult:
    external_event_id: str
    status: str


class CalendarProvider(ABC):
    @abstractmethod
    def connect(self, auth_code: str | None, redirect_uri: str | None) -> dict:
        raise NotImplementedError

    @abstractmethod
    def create_event(self, payload: CalendarEventInput) -> CalendarEventResult:
        raise NotImplementedError
