import pytest
from app.io_jsonl import normalize_username, normalize_phone, generate_message_id
from app.analysis.signals import extract_signals

def test_normalize_username():
    assert normalize_username("TestUser") == "testuser"
    assert normalize_username("MixedCase") == "mixedcase"

def test_normalize_phone():
    assert normalize_phone("+1 (202) 555-0123") == "+12025550123"
    assert normalize_phone("2025550123") == "2025550123"

def test_extract_signals():
    message = {"text": "is the streamer still dating sara?"}
    signals = extract_signals(message)
    
    assert "relationship_mentions" in signals
    assert signals["relationship_mentions"][0]["target"] == "sara"