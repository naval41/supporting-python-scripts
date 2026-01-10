from typing import TypedDict, List, Optional, Dict, Any

class FounderInfo(TypedDict):
    name: str
    title: str
    linkedin_url: Optional[str]
    twitter_url: Optional[str]
    email: Optional[str]
    phone: Optional[str]

class CompanyInfo(TypedDict):
    name: str
    linkedin_url: str
    domain: Optional[str]
    description: Optional[str]
    staff_strength: Optional[str] # e.g., "50-200"
    twitter_url: Optional[str]
    phone: Optional[str]
    founders: List[FounderInfo]
    
class AgentState(TypedDict):
    # Input
    company_name: str
    company_linkedin: str
    
    # State
    company_info: CompanyInfo
    retry_count: int
    is_valid: bool
    errors: List[str]
    
    # Internal logging
    logs: List[str]
