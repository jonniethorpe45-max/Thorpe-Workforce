from dataclasses import dataclass

from app.services import prompt_templates
from app.workers.definitions import get_worker_definition


@dataclass(frozen=True)
class PromptBundle:
    profile: str
    company_research = staticmethod(prompt_templates.company_research_prompt)
    outreach = staticmethod(prompt_templates.outreach_prompt)
    followup = staticmethod(prompt_templates.followup_prompt)
    reply_classification = staticmethod(prompt_templates.reply_classification_prompt)


_PROMPT_BUNDLES: dict[str, PromptBundle] = {
    "sales": PromptBundle(profile="sales"),
}


def get_prompt_bundle(worker_type: str) -> PromptBundle:
    try:
        definition = get_worker_definition(worker_type)
        profile = definition.prompt_profile
    except ValueError:
        profile = "sales"
    return _PROMPT_BUNDLES.get(profile, _PROMPT_BUNDLES["sales"])
