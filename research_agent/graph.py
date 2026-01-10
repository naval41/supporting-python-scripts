import json
import re
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_aws import ChatBedrock
from langgraph.graph import StateGraph, END

from .state import AgentState, CompanyInfo, FounderInfo
from .tools import ResearchTools

from util.config import Config

# Initialize Tools
tavily_tools = ResearchTools()

# Initialize LLM
aws_config = Config.load_aws_config()
bedrock_creds = aws_config.get("bedrock", {})

llm = ChatBedrock(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    model_kwargs={"temperature": 0},
    region_name=aws_config.get("region_name", "us-east-1"),
    aws_access_key_id=bedrock_creds.get("aws_access_key_id"),
    aws_secret_access_key=bedrock_creds.get("aws_secret_access_key")
)

def researcher_node(state: AgentState) -> AgentState:
    """
    Step 1: Gather general company info and identify founders.
    """
    company_name = state["company_name"]
    print(f"--- [Researcher] searching for {company_name} ---")
    
    # 1. Search Company Metadata
    comp_results = tavily_tools.search_company_info(company_name)
    
    # 2. Search Founders
    founder_results = tavily_tools.search_founders(company_name)
    
    # 3. Search Company Twitter
    twitter_results = tavily_tools.search_company_twitter(company_name)
    
    # 4. Search Company Phone
    phone_results = tavily_tools.search_company_phone(company_name)
    
    # 5. Use LLM to extract structured data from unstructured search results
    prompt = f"""
    You are a researcher. Extract the following information about the company '{company_name}' from the search results below.
    
    Search Results (Company): {json.dumps(comp_results.get('results', []))}
    Search Results (Founders): {json.dumps(founder_results.get('results', []))}
    Search Results (Twitter): {json.dumps(twitter_results.get('results', []))}
    Search Results (Phone): {json.dumps(phone_results.get('results', []))}
    
    Output JSON format:
    {{
        "domain": "string (website url)",
        "description": "string (brief summary)",
        "twitter_url": "string or null (prioritize x.com or twitter.com/profile)",
        "phone": "string or null (generic corporate number)",
        "staff_strength": "string (e.g. 10-50) or null",
        "founders": [
            {{ "name": "string", "title": "string (e.g. CEO)", "linkedin_url": "string or null" }}
        ]
    }}
    
    If founders are not clearly found, return empty list for them.
    """
    
    messages = [
        SystemMessage(content="You are a helpful research assistant. Return pure JSON."),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content
        # Basic cleanup if markdown backticks exist
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
             content = content.split("```")[1].split("```")[0]
             
        data = json.loads(content.strip())
        
        # Merge into state
        # Initialize company info object if not present, but preserve existing if we are looping
        current_info = state.get("company_info", {
            "name": company_name, 
            "linkedin_url": state["company_linkedin"], 
            "founders": []
        })
        
        current_info.update({
            "domain": data.get("domain"),
            "description": data.get("description"),
            "twitter_url": data.get("twitter_url"),
            "phone": data.get("phone"),
            "staff_strength": data.get("staff_strength")
        })
        
        # If we found new founders, add them. 
        # (In a real retry scenario, we'd be smarter about merging)
        if data.get("founders"):
            current_info["founders"] = data.get("founders")
            
        return {
            "company_info": current_info,
            "logs": state.get("logs", []) + [f"Researcher found basic info and {len(current_info['founders'])} potential founders."]
        }
        
    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"Researcher Error: {str(e)}"]
        }

def enricher_node(state: AgentState) -> AgentState:
    """
    Step 2: Enrich founder details (Email, Twitter).
    """
    info = state["company_info"]
    founders = info.get("founders", [])
    
    if not founders:
        return {"logs": state.get("logs", []) + ["No founders to enrich."]}
        
    print(f"--- [Enricher] enriching {len(founders)} founders ---")
    
    enriched_founders = []
    
    for founder in founders:
        name = founder.get("name")
        print(f"   Enriching: {name}")
        search_res = tavily_tools.enrich_founder(name, info["name"])
        twitter_res = tavily_tools.search_founder_twitter(name, info["name"])
        
        prompt = f"""
        Extract contact info for founder '{name}' of '{info['name']}' from results.
        
        Results: {json.dumps(search_res.get('results', []))}
        Twitter Results: {json.dumps(twitter_res.get('results', []))}
        
        Output JSON:
        {{
            "twitter_url": "string or null (prioritize x.com or twitter.com)",
            "email": "string or null",
            "phone": "string or null",
            "linkedin_url": "string or null (if better match found)"
        }}
        """
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            
            # Merge
            founder.update(data)
            # Ensure keys exist
            if "phone" not in founder: founder["phone"] = None
            if "email" not in founder: founder["email"] = None
            
            enriched_founders.append(founder)
        except:
            enriched_founders.append(founder) # Keep original if failed
    
    info["founders"] = enriched_founders
    return {"company_info": info}

def validator_node(state: AgentState) -> AgentState:
    """
    Step 3: Validate data quality and decide to retry or finish.
    """
    info = state["company_info"]
    errors = []
    
    print("--- [Validator] Checking data ---")
    
    # Check 1: Domain
    if not info.get("domain"):
        errors.append("Missing Company Domain")
        
    # Check 2: Founders
    if not info.get("founders"):
        errors.append("No Founders Identified")
        
    # Check 3: Twitter Validation
    twitter_url = info.get("twitter_url")
    if twitter_url:
        if not re.match(r"https?://(www\.)?(twitter\.com|x\.com)/.+", twitter_url):
             errors.append(f"Invalid Company Twitter URL: {twitter_url}")
             
    # Check 4: Staff Strength Format
    staff = info.get("staff_strength")
    if staff and not (any(c.isdigit() for c in staff) or len(staff) > 1):
        errors.append(f"Suspicious Staff Strength: {staff}")
        
    for founder in info.get("founders", []):
        f_twitter = founder.get("twitter_url")
        if f_twitter:
             if not re.match(r"https?://(www\.)?(twitter\.com|x\.com)/.+", f_twitter):
                 errors.append(f"Invalid Founder Twitter URL ({founder.get('name')}): {f_twitter}")
        
    state["is_valid"] = len(errors) == 0
    state["errors"] =  errors # Overwrite prev errors to reflect current state
    
    # Increment retry
    state["retry_count"] = state.get("retry_count", 0) + 1
    
    return state

def router(state: AgentState):
    """
    Decide next step.
    """
    if state["is_valid"]:
        return END
    
    if state["retry_count"] > 1: # Max 1 retry for now to save tokens/API calls
        return END
        
    return "researcher"

# Build Graph
graph_builder = StateGraph(AgentState)

graph_builder.add_node("researcher", researcher_node)
graph_builder.add_node("enricher", enricher_node)
graph_builder.add_node("validator", validator_node)

graph_builder.set_entry_point("researcher")

graph_builder.add_edge("researcher", "enricher")
graph_builder.add_edge("enricher", "validator")
graph_builder.add_conditional_edges("validator", router, {
    "researcher": "researcher",
    END: END
})

execution_graph = graph_builder.compile()
