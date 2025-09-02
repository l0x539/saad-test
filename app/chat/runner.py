import asyncio
import time
from typing import List
from app.chat.twitch_live import TwitchLiveClient
from app.chat.replay import ReplayClient

def run_chat_monitor(channels: List[str], duration_seconds: int, offline: bool = False):
    """Run chat monitor in live or offline mode"""
    if offline:
        client = ReplayClient(channels)
    else:
        client = TwitchLiveClient(channels)
    
    try:
        client.run(duration_seconds)
    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    except Exception as e:
        print(f"Error running chat monitor: {e}")