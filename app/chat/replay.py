import json
import time
from datetime import datetime
from typing import List
from app.io_jsonl import append_jsonl, generate_message_id
from app.analysis.signals import extract_signals
from app.analysis.rollups import update_profiles

class ReplayClient:
    def __init__(self, channels: List[str]):
        self.channels = channels
        self.messages_file = "data/logs/messages.jsonl"
    
    def run(self, duration_seconds: int):
        """Replay messages from fixtures"""
        start_time = time.time()
        
        for channel in self.channels:
            fixture_file = f"fixtures/chat/{channel}.jsonl"
            
            try:
                with open(fixture_file, 'r') as f:
                    for line in f:
                        if time.time() - start_time > duration_seconds:
                            return
                        
                        try:
                            message_data = json.loads(line.strip())
                            # Add missing fields
                            if "message_id" not in message_data:
                                message_data["message_id"] = generate_message_id(
                                    message_data["channel"],
                                    message_data["user_name"],
                                    message_data["text"],
                                    message_data["ts"]
                                )
                            if "mentions" not in message_data:
                                message_data["mentions"] = self.extract_mentions(message_data["text"])
                            if "urls" not in message_data:
                                message_data["urls"] = self.extract_urls(message_data["text"])
                            if "emotes" not in message_data:
                                message_data["emotes"] = []
                            if "source" not in message_data:
                                message_data["source"] = "fixture-replay"
                            
                            # Save message
                            append_jsonl(self.messages_file, message_data, "message_id")
                            
                            # Extract signals and update profiles
                            signals = extract_signals(message_data)
                            update_profiles(message_data, signals)
                            
                            # Small delay to mimic real chat
                            time.sleep(0.1)
                            
                        except json.JSONDecodeError:
                            continue
            except FileNotFoundError:
                print(f"Fixture file not found: {fixture_file}")
                continue
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text (simplified)"""
        import re
        mention_pattern = r'@(\w+)'
        return re.findall(mention_pattern, text)
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text (simplified)"""
        import re
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, text)