import pytest
from app.providers.gravatar_like import GravatarLikeProvider
from app.providers.handle_presence import HandlePresenceProvider

def test_gravatar_provider():
    provider = GravatarLikeProvider()
    subject = {
        "type": "email",
        "value": "test@example.com",
        "normalized_value": "test@example.com",
        "key": "email_test@example.com"
    }
    
    result = provider.enrich(subject)
    assert "avatar_url" in result
    assert "exists" in result

def test_handle_presence_provider():
    provider = HandlePresenceProvider()
    subject = {
        "type": "username",
        "value": "someuser",
        "normalized_value": "someuser",
        "key": "username_someuser"
    }
    
    result = provider.enrich(subject)
    assert "platforms" in result
    assert "exists" in result