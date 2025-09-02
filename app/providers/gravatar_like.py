import hashlib
from app.providers.base import Provider

class GravatarLikeProvider:
    def __init__(self):
        self.name = "gravatar_like"
        self.supports = {"email"}
    
    def enrich(self, subject: dict) -> dict:
        if subject["type"] != "email":
            return {"error": "Unsupported subject type"}
        
        email = subject["normalized_value"]
        email_hash = hashlib.md5(email.encode()).hexdigest()
        
        return {
            "exists": True,  # Simulated
            "avatar_url": f"https://www.gravatar.com/avatar/{email_hash}?d=identicon",
            "profile_url": f"https://www.gravatar.com/{email_hash}"
        }