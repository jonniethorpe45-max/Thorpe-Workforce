from app.integrations.ai.mock_provider import MockAIProvider


def test_message_generation_service():
    provider = MockAIProvider()
    result = provider.generate_outreach_email(
        lead_name="Jordan",
        company_name="Nimbus",
        title="VP Sales",
        cta="Would a short intro help?",
    )
    assert "Nimbus" in result.subject
    assert "Jordan" in result.body


def test_reply_classification_service():
    provider = MockAIProvider()
    result = provider.classify_reply("Thanks, interested in learning more.")
    assert result.intent == "interested"
    assert result.confidence > 0.8
