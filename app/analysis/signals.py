import re
from typing import Dict, Any, List

def extract_signals(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract signals from message text"""
    text = message_data.get("text", "").lower()
    signals = {}
    
    # Relationship detection
    relationship_patterns = [
        r'(still\s+)?dating\s+(\w+)',
        r'(is|are)\s+(he|she|they|streamer)\s+dating\s+(\w+)',
        r'(he|she|they|streamer)\'s\s+dating\s+(\w+)'
    ]
    
    relationship_evidence = []
    for pattern in relationship_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            target = match.group(2) if match.lastindex >= 2 else match.group(1)
            if target and len(target) > 2:  # Avoid very short matches
                relationship_evidence.append({
                    "target": target,
                    "snippet": match.group(0),
                    "pattern": pattern
                })
    
    if relationship_evidence:
        signals["relationship_mentions"] = relationship_evidence
    
    return signals