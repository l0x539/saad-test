import pytest
import json
import tempfile
import os
from app.analysis.rollups import update_user_profile, update_channel_profile
from app.analysis.signals import extract_signals

def test_update_user_profile():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test message
        message = {
            "ts": "2025-09-02T12:34:56Z",
            "channel": "test_channel",
            "user_name": "testuser",
            "text": "is the streamer dating sara?",
            "mentions": [],
            "urls": [],
            "emotes": [],
            "source": "test"
        }
        
        # Extract signals
        signals = extract_signals(message)
        
        # Update profile
        profile_path = os.path.join(temp_dir, "testuser.json")
        os.makedirs(os.path.dirname(profile_path), exist_ok=True)
        
        # This would need to be adapted to work with the file system
        # For now, just test that the function doesn't crash
        try:
            update_user_profile(message, signals)
            assert True
        except:
            assert False

def test_update_channel_profile():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test message
        message = {
            "ts": "2025-09-02T12:34:56Z",
            "channel": "test_channel",
            "user_name": "testuser",
            "text": "is the streamer dating sara?",
            "mentions": [],
            "urls": [],
            "emotes": [],
            "source": "test"
        }
        
        # Extract signals
        signals = extract_signals(message)
        
        # Update profile
        profile_path = os.path.join(temp_dir, "test_channel.json")
        os.makedirs(os.path.dirname(profile_path), exist_ok=True)
        
        # This would need to be adapted to work with the file system
        try:
            update_channel_profile(message, signals)
            assert True
        except:
            assert False