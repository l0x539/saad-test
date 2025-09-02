import json
import os
from pathlib import Path
from typing import List, Iterator
import hashlib

def ensure_directory(path: str):
    """Ensure directory exists"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def append_jsonl(file_path: str, data: dict, id_field: str = None):
    """Append a JSON record to a JSONL file, checking for duplicates"""
    ensure_directory(file_path)
    
    # Check for duplicates if id_field is provided
    if id_field and id_field in data:
        if is_duplicate(file_path, id_field, data[id_field]):
            return False
    
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')
    return True

def is_duplicate(file_path: str, id_field: str, id_value: str) -> bool:
    """Check if a record with the given ID already exists"""
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                if record.get(id_field) == id_value:
                    return True
            except json.JSONDecodeError:
                continue
    return False

def read_jsonl(file_path: str) -> Iterator[dict]:
    """Read JSONL file line by line"""
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                yield json.loads(line.strip())
            except json.JSONDecodeError:
                continue

def normalize_username(username: str) -> str:
    """Normalize username to lowercase"""
    return username.lower()

def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format (simplified)"""
    # Remove all non-digit characters except leading +
    if phone.startswith('+'):
        cleaned = '+' + ''.join(c for c in phone[1:] if c.isdigit())
    else:
        cleaned = ''.join(c for c in phone if c.isdigit())
    return cleaned

def generate_message_id(channel: str, user_name: str, text: str, ts: str) -> str:
    """Generate a unique message ID"""
    content = f"{channel}:{user_name}:{text}:{ts}"
    return hashlib.md5(content.encode()).hexdigest()