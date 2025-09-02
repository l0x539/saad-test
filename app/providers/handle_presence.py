import json
import os
from app.providers.base import Provider

class HandlePresenceProvider:
    def __init__(self):
        self.name = "handle_presence"
        self.supports = {"username"}
        self.handles_data = self.load_handles_data()
    
    def load_handles_data(self):
        """Load handles data from fixtures"""
        handles_file = "fixtures/handles.json"
        try:
            with open(handles_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def enrich(self, subject: dict) -> dict:
        if subject["type"] != "username":
            return {"error": "Unsupported subject type"}
        
        username = subject["normalized_value"]
        platforms = self.handles_data.get(username, [])
        
        return {
            "exists": len(platforms) > 0,
            "platforms": platforms,
            "platform_count": len(platforms)
        }