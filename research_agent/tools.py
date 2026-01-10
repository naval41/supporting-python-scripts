import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from tavily import TavilyClient

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent.parent))

from util.config import Config

class ResearchTools:
    def __init__(self):
        config = Config.load_config()
        api_key = config.get("tavily", {}).get("api_key")
        
        if not api_key or "YOUR_ARC_HERE" in api_key:
             # Fallback to environment variable or raising helpful error if missing
            api_key = os.environ.get("TAVILY_API_KEY")

        if not api_key:
            raise ValueError("Tavily API key is missing. Please add it to config.json or set TAVILY_API_KEY env var.")
            
        self.client = TavilyClient(api_key=api_key)

    def search_company_info(self, company_name: str) -> Dict[str, Any]:
        """
        Search for general company info: domain, twitter, staff strength (approx).
        """
        query = f"{company_name} official website twitter staff count"
        try:
            # Using basic search for breadth
            response = self.client.search(query=query, search_depth="advanced", max_results=5)
            return response
        except Exception as e:
            return {"error": str(e), "results": []}

    def search_founders(self, company_name: str) -> Dict[str, Any]:
        """
        Search for founders of the company.
        """
        query = f"who are the founders of {company_name} linkedin"
        try:
            response = self.client.search(query=query, search_depth="advanced", max_results=5)
            return response
        except Exception as e:
            return {"error": str(e), "results": []}

    def enrich_founder(self, founder_name: str, company_name: str) -> Dict[str, Any]:
        """
        Search for specific contact details or social profiles for a founder.
        """
        # Targeted query for contacts (best effort)
        query = f"{founder_name} {company_name} email twitter linkedin contact"
        try:
            response = self.client.search(query=query, search_depth="advanced", max_results=5)
            return response
        except Exception as e:
            return {"error": str(e), "results": []}

    def search_company_twitter(self, company_name: str) -> Dict[str, Any]:
        """
        Search specifically for company's Twitter/X profile.
        """
        query = f"site:twitter.com {company_name} official profile OR site:x.com {company_name} official profile"
        try:
            response = self.client.search(query=query, search_depth="advanced", max_results=3)
            return response
        except Exception as e:
            return {"error": str(e), "results": []}

    def search_founder_twitter(self, founder_name: str, company_name: str) -> Dict[str, Any]:
        """
        Search specifically for founder's Twitter/X profile.
        """
        query = f"site:twitter.com {founder_name} {company_name} OR site:x.com {founder_name} {company_name}"
        try:
            res = self.client.search(query=query, search_depth="advanced", max_results=3)
            return res
        except Exception as e:
            return {"error": str(e), "results": []}

    def search_company_phone(self, company_name: str) -> Dict[str, Any]:
        """
        Search for company's generic phone number (HQ, Support).
        """
        query = f"{company_name} corporate phone number head office contact support"
        try:
            response = self.client.search(query=query, search_depth="advanced", max_results=3)
            return response
        except Exception as e:
            return {"error": str(e), "results": []}
