from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SendEmailInput:
    to_email: str
    subject: str
    body: str


@dataclass
class SendEmailResult:
    provider_message_id: str
    status: str


class EmailProvider(ABC):
    @abstractmethod
    def send_email(self, payload: SendEmailInput) -> SendEmailResult:
        raise NotImplementedError
