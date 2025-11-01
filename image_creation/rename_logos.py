import os
import csv
import re
from pathlib import Path
from difflib import SequenceMatcher

def load_company_data(csv_file):
    """Load company data from CSV file"""
    companies = {}
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies[row['name']] = row['slug']
    return companies

def clean_filename(filename):
    """Clean filename by removing extension and common suffixes"""
    # Remove file extension
    name = os.path.splitext(filename)[0]
    
    # Remove common suffixes
    suffixes_to_remove = [
        '_BIG', '.BIG', '_BIG.D', '.BIG.D', '.D', '_D',
        '_seeklogo', '-seeklogo', '_icon', '-icon',
        '_logo', '-logo', '_png', '-png'
    ]
    
    for suffix in suffixes_to_remove:
        if name.upper().endswith(suffix.upper()):
            name = name[:-len(suffix)]
    
    # Remove numbers in parentheses like (1)
    name = re.sub(r'\(\d+\)', '', name)
    
    # Remove extra spaces and dots
    name = name.strip(' .')
    
    return name

def create_mapping_rules():
    """Create manual mapping rules for logos that don't match directly"""
    return {
        # Stock symbols to company names
        'GS': 'Goldman Sachs',
        'PANW': 'Palo Alto Networks',
        'DASH': 'DoorDash',
        'GRPN': 'Groupon',
        'MMYT': 'Make My Trip',
        'EXPE': 'Expedia',
        'GRAB': 'Grab',
        'PYPL': 'PayPal',
        'TWKS': 'Thoughtworks',
        'LYFT': 'Lyft',
        'LNKD': 'LinkedIn',
        'AMZN': 'Amazon',
        'UBER': 'Uber',
        'ASAN': 'Asana',
        'BOX': 'Box',
        'FRSH': 'Freshworks',
        'PATH': 'PathAI',
        'DBX': 'Dropbox',
        'G': 'Google',
        'ESTC': 'Elastic',
        'EPAM': 'EPAM',
        'MNDY': 'Monday.com',
        'TWLO': 'Twilio',
        'ZM': 'Zoom',
        'WDAY': 'Workday',
        'INTU': 'Intuit',
        'ADP': 'ADP',
        'SHOP': 'Shopify',
        'NOW': 'ServiceNow',
        'ADBE': 'Adobe',
        'NVDA': 'Nvidia',
        'IBM': 'IBM',
        'CSCO': 'Cisco',
        'NFLX': 'Netflix',
        'ORCL': 'Oracle',
        'WMT': 'Walmart',
        'TSLA': 'Tesla',
        'V': 'Visa',
        'SWIGGY': 'Swiggy',
        'SNAP': 'Snap Inc.',
        'SNOW': 'Snowflake',
        'SPOT': 'Spotify',
        'SAP': 'SAP',
        'MDB': 'MongoDB',
        'MU': 'Micron Technology',
        'MA': 'MasterCard',
        'META': 'Meta',
        'MSFT': 'Microsoft',
        'DOX': 'Amdocs',
        'TEAM': 'Atlassian',
        'ACN': 'Accenture',
        'WORK': 'Slack',
        'AAPL': 'Apple',
        'CRM': 'Salesforce',
        'HackerRank': 'HackerRank',
        'DELHIVERY': 'Delhivery',
        'PayU': 'PayU',
        'Zeta': 'Zeta',
        'Twitter': 'Twitter',
        'HackerRank': 'HackerRank',
        'bloomberg': 'Bloomberg LP',
        'bytedance': 'ByteDance',
        'flipkart': 'Flipkart',
        'Booking': 'Booking.com',
        'zepto': 'Zepto',
        'ola-cabs': 'Ola',
        'phonepe': 'PhonePe',
        'google-cloud': 'Google Cloud',
        'google-deepmind': 'Google DeepMind',
        'google-youtube': 'Google (YouTube)',
        'google': 'Google',
        'vecteezy_disney-plus-hotstar-app-icon_46437279': 'Disney+ Hotstar',
        'hotstar-logo-png_seeklogo-360295': 'Disney+ Hotstar',
        'img': 'Unknown',  # Generic placeholder
        'Logo': 'Unknown'  # Generic placeholder
    }

def find_best_match(logo_name, companies, mapping_rules):
    """Find the best matching company for a logo"""
    # First try exact match with mapping rules
    if logo_name in mapping_rules:
        company_name = mapping_rules[logo_name]
        if company_name in companies:
            return company_name, companies[company_name]
    
    # Try direct match with company names
    for company_name in companies.keys():
        if logo_name.lower() == company_name.lower():
            return company_name, companies[company_name]
    
    # Try partial matching
    best_match = None
    best_score = 0
    
    for company_name in companies.keys():
        # Clean company name for comparison
        clean_company = re.sub(r'[^\w\s]', '', company_name.lower())
        clean_logo = re.sub(r'[^\w\s]', '', logo_name.lower())
        
        # Calculate similarity
        score = SequenceMatcher(None, clean_logo, clean_company).ratio()
        
        if score > best_score and score > 0.6:  # Threshold for matching
            best_score = score
            best_match = company_name
    
    if best_match:
        return best_match, companies[best_match]
    
    return None, None

def rename_logos(logos_dir, csv_file, dry_run=True):
    """Rename logo files based on company mapping"""
    companies = load_company_data(csv_file)
    mapping_rules = create_mapping_rules()
    
    logo_files = [f for f in os.listdir(logos_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    print(f"Found {len(logo_files)} logo files")
    print(f"Loaded {len(companies)} companies from CSV")
    print(f"Dry run mode: {'ON' if dry_run else 'OFF'}")
    print("-" * 80)
    
    successful_matches = []
    failed_matches = []
    
    for logo_file in logo_files:
        # Clean the logo filename
        clean_name = clean_filename(logo_file)
        
        # Find best match
        company_name, slug = find_best_match(clean_name, companies, mapping_rules)
        
        if company_name and slug:
            new_filename = f"{slug}.png"
            old_path = os.path.join(logos_dir, logo_file)
            new_path = os.path.join(logos_dir, new_filename)
            
            if dry_run:
                print(f"✅ MATCH: {logo_file} -> {new_filename} (Company: {company_name})")
            else:
                try:
                    os.rename(old_path, new_path)
                    print(f"✅ RENAMED: {logo_file} -> {new_filename} (Company: {company_name})")
                except Exception as e:
                    print(f"❌ ERROR renaming {logo_file}: {e}")
            
            successful_matches.append((logo_file, new_filename, company_name))
        else:
            print(f"❌ NO MATCH: {logo_file} (cleaned: {clean_name})")
            failed_matches.append(logo_file)
    
    print("-" * 80)
    print(f"SUMMARY:")
    print(f"✅ Successful matches: {len(successful_matches)}")
    print(f"❌ Failed matches: {len(failed_matches)}")
    
    if failed_matches:
        print(f"\nFailed matches:")
        for failed in failed_matches:
            print(f"  - {failed}")
    
    return successful_matches, failed_matches

if __name__ == "__main__":
    # Configuration
    logos_dir = "logos"
    csv_file = "Prod_DB_V4__Company_.csv"
    
    # First run in dry-run mode
    print("🚀 DRY RUN MODE - No files will be renamed")
    print("=" * 80)
    successful, failed = rename_logos(logos_dir, csv_file, dry_run=True)
    
    # Ask user if they want to proceed with actual renaming
    if successful:
        print(f"\n💡 Found {len(successful)} matches that can be renamed.")
        response = input("\nDo you want to proceed with actual renaming? (y/N): ")
        
        if response.lower() in ['y', 'yes']:
            print("\n🔄 PROCEEDING WITH ACTUAL RENAMING")
            print("=" * 80)
            rename_logos(logos_dir, csv_file, dry_run=False)
        else:
            print("❌ Renaming cancelled by user.")
    else:
        print("❌ No matches found. Please review the mapping rules.") 