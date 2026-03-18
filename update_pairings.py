import requests
import csv
import json
import os
from datetime import datetime

# Your Google Sheets published CSV URLs
SECTIONS = {
    'champ': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRbkBzRLYMKbxSExTSfcnwwq_PLfVwYQqYI2IiM4Vk8jCYPZuxcgpE845B_CRHNaNxL9H_htfY_ngd1/pub?gid=1357065481&single=true&output=csv',
    'reserve': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRbkBzRLYMKbxSExTSfcnwwq_PLfVwYQqYI2IiM4Vk8jCYPZuxcgpE845B_CRHNaNxL9H_htfY_ngd1/pub?gid=1553676826&single=true&output=csv',
    'novice': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRbkBzRLYMKbxSExTSfcnwwq_PLfVwYQqYI2IiM4Vk8jCYPZuxcgpE845B_CRHNaNxL9H_htfY_ngd1/pub?gid=1771561312&single=true&output=csv'
}

def fetch_and_transform(section_name, csv_url):
    """Fetch a pairing sheet and convert to clean JSON format"""
    
    print(f"Fetching {section_name}...")
    
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV
        reader = csv.reader(response.text.splitlines())
        rows = list(reader)
        
        # Extract metadata
        tournament_title = rows[1][0] if len(rows) > 1 else "Chess Tournament"
        round_info = rows[2][0] if len(rows) > 2 else "Round 1"
        
        print(f"  Title: {tournament_title}")
        print(f"  Round: {round_info}")
        
        # Parse pairings (starting from row 4, index 3)
        pairings = []
        
        for row in rows[3:]:
            # Check if this row has a board number in column A
            if len(row) >= 5 and row[0] and row[0].strip().isdigit():
                
                # Get results independently from columns B and D
                white_result = row[1].strip().upper() if len(row) > 1 else ''
                black_result = row[3].strip().upper() if len(row) > 3 else ''
                
                # Validate results
                valid_results = ['W', 'L', 'D', 'X', 'F', '½', '0', '1', '']
                if white_result not in valid_results:
                    white_result = ''
                if black_result not in valid_results:
                    black_result = ''
                
                pairing = {
                    'board': int(row[0]),
                    'white_player': row[2].strip() if len(row) > 2 else '',
                    'white_result': white_result,
                    'black_player': row[4].strip() if len(row) > 4 else '',
                    'black_result': black_result,
                    'section': section_name
                    # REMOVED 'round' from individual pairings
                }
                
                # Only include if at least one player name exists
                if pairing['white_player'] or pairing['black_player']:
                    pairings.append(pairing)
        
        print(f"  Found {len(pairings)} pairings")
        
        return {
            'tournament': tournament_title,
            'round': round_info,  # Round info stored ONCE at section level
            'last_updated': datetime.now().isoformat(),
            'section': section_name,
            'pairings': pairings
        }
        
    except Exception as e:
        print(f"  Error: {e}")
        return None

# Create output directory
os.makedirs('public/data', exist_ok=True)
print("Created public/data directory")

# Process all sections
all_data = {}

for section_name, url in SECTIONS.items():
    print(f"\n--- Processing {section_name} ---")
    section_data = fetch_and_transform(section_name, url)
    
    if section_data:
        all_data[section_name] = section_data
        
        # Save individual section file
        with open(f'public/data/{section_name}_pairings.json', 'w', encoding='utf-8') as f:
            json.dump(section_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Saved {section_name}_pairings.json")

# Save combined data
with open('public/data/all_pairings.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Update complete! Files saved to public/data/")
print(f"   Sections processed: {', '.join(SECTIONS.keys())}")