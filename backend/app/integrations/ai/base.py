from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CompanyResearchResult:
    summary: str
    pain_points: list[str]
    relevance_score: float
    personalization_hook: str
    model: str


@dataclass
class OutreachEmailResult:
    subject: str
    body: str
    personalization: dict


@dataclass
class ReplyClassificationResult:
    intent: str
    confidence: float
    requires_human_review: bool
    sentiment: str


class AIProvider(ABC):
    @abstractmethod
    def generate_company_research(self, company_name: str, website: str | None, industry: str | None) -> CompanyResearchResult:
        raise NotImplementedError

    @abstractmethod
    def generate_outreach_email(self, lead_name: str, company_name: str, title: str | None, cta: str) -> OutreachEmailResult:
        raise NotImplementedError

    @abstractmethod
    def generate_followup_email(self, lead_name: str, company_name: str, step: int, cta: str) -> OutreachEmailResult:
        raise NotImplementedError

    @abstractmethod
    def classify_reply(self, reply_text: str) -> ReplyClassificationResult:
        raise NotImplementedError

    @abstractmethod
    def generate_booking_response(self, lead_name: str) -> str:
        raise NotImplementedError
