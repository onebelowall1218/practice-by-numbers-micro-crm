"""Tests the Jev response-to-Judgment conversion with fake SDK objects. No network calls."""

from types import SimpleNamespace

from app.services.ai.providers.jev_typesafe import URGENCY_LEVELS, _to_judgment


def fake_response(
    *, priority="high", waiting_on="us", needs_attention=0.8, urgency=2.0, confidence=0.7
):
    """A stand-in for typesafe_sdk.SystemOneResponse with the same .choices/.nouls/.scores shape."""
    return SimpleNamespace(
        choices={
            "priority": SimpleNamespace(choice=priority, confidence=confidence),
            "waiting_on": SimpleNamespace(choice=waiting_on, confidence=confidence),
        },
        nouls={"needs_attention": SimpleNamespace(noul=needs_attention)},
        scores={"urgency": SimpleNamespace(score=urgency, confidence=confidence)},
    )


def test_choice_answers_map_directly_onto_priority_and_waiting_on():
    judgment = _to_judgment(fake_response(priority="medium", waiting_on="customer"))
    assert judgment.priority == "medium"
    assert judgment.waiting_on == "customer"


def test_needs_attention_is_true_at_or_above_fifty_percent():
    assert _to_judgment(fake_response(needs_attention=0.5)).needs_attention is True
    assert _to_judgment(fake_response(needs_attention=0.49)).needs_attention is False


def test_urgency_score_is_normalised_to_the_zero_to_one_range():
    top_level = len(URGENCY_LEVELS) - 1
    assert _to_judgment(fake_response(urgency=0.0)).urgency_score == 0.0
    assert _to_judgment(fake_response(urgency=top_level)).urgency_score == 1.0
    assert _to_judgment(fake_response(urgency=top_level / 2)).urgency_score == 0.5


def test_confidence_comes_from_the_priority_choice():
    assert _to_judgment(fake_response(confidence=0.42)).confidence == 0.42
