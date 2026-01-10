import csv
import argparse
import sys
import json
from pathlib import Path
from typing import List

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from research_agent.graph import execution_graph

def read_input_csv(file_path: str) -> List[dict]:
    companies = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)
    return companies

def main():
    parser = argparse.ArgumentParser(description="Run Research Agent")
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", default="enriched_companies.csv", help="Output CSV file path")
    args = parser.parse_args()
    
    inputs = read_input_csv(args.input)
    results = []
    
    print(f"Starting research on {len(inputs)} companies...")
    
    for row in inputs:
        company_name = row.get("Company Name") or row.get("name")
        linkedin_url = row.get("LinkedIn URL") or row.get("linkedin_url")
        
        if not company_name:
            print("Skipping row without company name")
            continue
            
        print(f"\nPROCESSING: {company_name}")
        
        initial_state = {
            "company_name": company_name,
            "company_linkedin": linkedin_url,
            "retry_count": 0,
            "logs": [],
            "errors": []
        }
        
        try:
            final_state = execution_graph.invoke(initial_state)
            info = final_state.get("company_info", {})
            
            # Flatten for CSV
            # If multiple founders, we might make multiple rows or semicolon separate. 
            # Requirement says "Founder details with Email, Phone..."
            # Let's flatten the first founder primarily, or aggregate.
            
            founders = info.get("founders", [])
            f_names = "; ".join([f.get("name", "") for f in founders])
            f_emails = "; ".join([f.get("email", "") for f in founders if f.get("email")])
            f_phones = "; ".join([f.get("phone", "") for f in founders if f.get("phone")])
            f_linkedins = "; ".join([f.get("linkedin_url", "") for f in founders if f.get("linkedin_url")])
            f_twitters = "; ".join([f.get("twitter_url", "") for f in founders if f.get("twitter_url")])
            
            result_row = {
                "Input Company": company_name,
                "Domain": info.get("domain", ""),
                "Description": info.get("description", ""),
                "Staff Strength": info.get("staff_strength", ""),
                "Company LinkedIn": info.get("linkedin_url", ""),
                "Company Twitter": info.get("twitter_url", ""),
                "Company Phone": info.get("phone", ""),
                "Founder Names": f_names,
                "Founder Emails": f_emails,
                "Founder Phones": f_phones,
                "Founder LinkedIns": f_linkedins,
                "Founder Twitters": f_twitters,
                "Errors": "; ".join(final_state.get("errors", []))
            }
            results.append(result_row)
            
        except Exception as e:
            print(f"Error processing {company_name}: {e}")
            
    # Write Output
    if results:
        fieldnames = results[0].keys()
        with open(args.output, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResearch complete. Results saved to {args.output}")
    else:
        print("No results generated.")

if __name__ == "__main__":
    main()
