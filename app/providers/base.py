from typing import Protocol, Dict, Any, Set

class Provider(Protocol):
    name: str
    supports: Set[str]
    
    def enrich(self, subject: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich subject data and return enrichment result"""