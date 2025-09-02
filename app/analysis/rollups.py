import json
import os
from collections import Counter
from datetime import datetime
from typing import Dict, Any, List

from app.models import UserProfile, ChannelProfile


def _tokenize_keywords(text: str) -> List[str]:
    """Very simple tokenizer for top keywords; excludes trivial short tokens."""
    tokens = [t.strip().lower() for t in text.split() if len(t.strip()) > 2]
    return [t for t in tokens if t.isascii()]


def update_user_profile(message: Dict[str, Any], signals: Dict[str, Any]) -> None:
    """Create or update a user profile incrementally based on a single message."""
    user_name = message.get("user_name", "").lower()
    if not user_name:
        return

    profile_path = os.path.join("data", "profiles", "users", f"{user_name}.json")
    os.makedirs(os.path.dirname(profile_path), exist_ok=True)

    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile = UserProfile(**data)
        except Exception:
            profile = UserProfile(user_name=user_name)
    else:
        profile = UserProfile(user_name=user_name)

    # Update aggregates
    channel = message.get("channel", "").lower()
    if channel and channel not in profile.channels_participated:
        profile.channels_participated.append(channel)
    profile.message_count += 1

    # Update top keywords naively
    keywords = Counter(profile.top_keywords)
    for token in _tokenize_keywords(message.get("text", "")):
        keywords[token] += 1
    # Keep top 20
    profile.top_keywords = [k for k, _ in keywords.most_common(20)]

    # Last seen
    try:
        profile.last_seen = datetime.fromisoformat(message["ts"].replace("Z", "+00:00"))
    except Exception:
        pass

    # Facts from signals (very lightweight merge)
    if signals.get("relationship_mentions"):
        facts = profile.facts or {}
        facts.setdefault("asked_about_streamer_relationship", True)
        targets = [e.get("target") for e in signals["relationship_mentions"] if e.get("target")]
        facts.setdefault("suspected_relationship_targets", [])
        for t in targets:
            if t not in facts["suspected_relationship_targets"]:
                facts["suspected_relationship_targets"].append(t)
        facts.setdefault("evidence", [])
        facts["evidence"].append({
            "ts": message.get("ts"),
            "channel": channel,
            "snippet": signals["relationship_mentions"][0].get("snippet", "")
        })
        profile.facts = facts

    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(mode="json"), f, indent=2)


def update_channel_profile(message: Dict[str, Any], signals: Dict[str, Any]) -> None:
    """Create or update a channel profile incrementally based on a single message."""
    channel = message.get("channel", "").lower()
    if not channel:
        return

    profile_path = os.path.join("data", "profiles", "channels", f"{channel}.json")
    os.makedirs(os.path.dirname(profile_path), exist_ok=True)

    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile = ChannelProfile(**data)
        except Exception:
            profile = ChannelProfile(channel=channel)
    else:
        profile = ChannelProfile(channel=channel)

    profile.message_count += 1

    user_name = message.get("user_name", "").lower()
    if user_name and user_name not in profile.top_users:
        profile.top_users.append(user_name)

    # Update simple keyword list
    keywords = Counter(profile.top_keywords)
    for token in _tokenize_keywords(message.get("text", "")):
        keywords[token] += 1
    profile.top_keywords = [k for k, _ in keywords.most_common(20)]

    try:
        profile.last_seen = datetime.fromisoformat(message["ts"].replace("Z", "+00:00"))
    except Exception:
        pass

    # Streamer signals
    if signals.get("relationship_mentions"):
        rel_key = "relationship_mentions"
        existing = profile.streamer_signals.get(rel_key, [])
        # Merge by target and snippet counts in a very simple way
        for ev in signals[rel_key]:
            # Try to find existing entry for target
            found = False
            for entry in existing:
                if entry.get("target") == ev.get("target"):
                    entry.setdefault("evidence_count", 0)
                    entry["evidence_count"] += 1
                    entry.setdefault("examples", [])
                    if ev.get("snippet") and ev["snippet"] not in entry["examples"]:
                        entry["examples"].append(ev["snippet"])
                    found = True
                    break
            if not found:
                existing.append({
                    "target": ev.get("target"),
                    "evidence_count": 1,
                    "examples": [ev.get("snippet")] if ev.get("snippet") else []
                })
        profile.streamer_signals[rel_key] = existing

    # Unique users is approximated by length of top_users list
    profile.unique_users = len(profile.top_users)

    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(mode="json"), f, indent=2)


def update_profiles(message: Dict[str, Any], signals: Dict[str, Any]) -> None:
    """Helper to update both user and channel profiles for a message."""
    update_user_profile(message, signals)
    update_channel_profile(message, signals)