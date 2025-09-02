import typer
from typing import List, Optional
from datetime import datetime
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.models import Subject, SubjectType
from app.io_jsonl import append_jsonl, read_jsonl, normalize_username, normalize_phone
from app.chat.runner import run_chat_monitor
from app.providers.gravatar_like import GravatarLikeProvider
from app.providers.handle_presence import HandlePresenceProvider

app = typer.Typer()

@app.command()
def subjects_load(path: str = typer.Option(..., "--path", help="Path to subjects CSV file")):
    """Load subjects from CSV file"""
    subjects = []
    subjects_file = "data/subjects.json"
    
    try:
        with open(path, 'r') as f:
            # Skip header
            next(f)
            for line in f:
                if line.strip():
                    type_str, value = line.strip().split(',', 1)
                    subject_type = SubjectType(type_str)
                    
                    # Normalize value
                    if subject_type == SubjectType.USERNAME:
                        normalized_value = normalize_username(value)
                        key = f"username_{normalized_value}"
                    elif subject_type == SubjectType.PHONE:
                        normalized_value = normalize_phone(value)
                        key = f"phone_{normalized_value}"
                    else:  # email
                        normalized_value = value.lower()
                        key = f"email_{normalized_value}"
                    
                    subject = Subject(
                        type=subject_type,
                        value=value,
                        normalized_value=normalized_value,
                        key=key
                    )
                    subjects.append(subject.model_dump())
        
        # Write to subjects.json
        os.makedirs(os.path.dirname(subjects_file), exist_ok=True)
        with open(subjects_file, 'w') as f:
            json.dump(subjects, f, indent=2)
        
        typer.echo(f"Loaded {len(subjects)} subjects to {subjects_file}")
        
        # Run enrichment
        run_enrichment(subjects)
        
    except Exception as e:
        typer.echo(f"Error loading subjects: {e}", err=True)
        raise typer.Exit(1)

    # Note: removed duplicate definition of subjects_load

def run_enrichment(subjects: List[dict]):
    """Run enrichment on all subjects"""
    gravatar_provider = GravatarLikeProvider()
    handle_provider = HandlePresenceProvider()
    
    for subject in subjects:
        results = {}
        
        if subject['type'] in gravatar_provider.supports:
            results[gravatar_provider.name] = gravatar_provider.enrich(subject)
        
        if subject['type'] in handle_provider.supports:
            results[handle_provider.name] = handle_provider.enrich(subject)
        
        # Save enrichment results
        enrichment_file = f"data/enrichment/{subject['key']}.json"
        os.makedirs(os.path.dirname(enrichment_file), exist_ok=True)
        with open(enrichment_file, 'w') as f:
            json.dump(results, f, indent=2)

@app.command()
def chat_run(
    channels: List[str] = typer.Option(..., "--channels", help="Comma-separated list of channels"),
    duration_seconds: int = typer.Option(..., "--duration-seconds", help="Duration to run in seconds"),
    offline: bool = typer.Option(False, "--offline", help="Use offline mode with fixtures")
):
    """Run chat monitor for specified channels"""
    run_chat_monitor(channels, duration_seconds, offline)

@app.command()
def search_messages(
    by: str = typer.Option(..., "--by", help="Search by 'user' or 'channel'"),
    value: str = typer.Option(..., "--value", help="Value to search for"),
    since: Optional[str] = typer.Option(None, "--since", help="Start time (ISO8601)"),
    until: Optional[str] = typer.Option(None, "--until", help="End time (ISO8601)"),
    contains: Optional[str] = typer.Option(None, "--contains", help="Text to search for"),
    limit: int = typer.Option(100, "--limit", help="Maximum number of results")
):
    """Search messages with various filters"""
    messages_file = "data/logs/messages.jsonl"
    results = []
    
    try:
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00')) if since else None
        until_dt = datetime.fromisoformat(until.replace('Z', '+00:00')) if until else None
    except ValueError:
        typer.echo("Error: Invalid date format. Use ISO8601 format.", err=True)
        raise typer.Exit(1)
    
    for message in read_jsonl(messages_file):
        # Apply filters
        if by == "user" and message.get("user_name", "").lower() != value.lower():
            continue
        if by == "channel" and message.get("channel", "").lower() != value.lower():
            continue
        
        if since_dt and datetime.fromisoformat(message["ts"].replace('Z', '+00:00')) < since_dt:
            continue
        if until_dt and datetime.fromisoformat(message["ts"].replace('Z', '+00:00')) > until_dt:
            continue
        
        if contains and contains.lower() not in message.get("text", "").lower():
            continue
        
        results.append(message)
        if len(results) >= limit:
            break
    
    typer.echo(json.dumps(results, indent=2))

if __name__ == "__main__":
    app()