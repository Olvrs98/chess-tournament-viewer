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
    
    print(f"\n{'='*50}")
    print(f"🔍 PROCESSING SECTION: {section_name.upper()}")
    print(f"{'='*50}")
    print(f"📡 Fetching from URL: {csv_url}")
    
    try:
        # Step 1: Download the CSV
        print("⏳ Downloading CSV...")
        response = requests.get(csv_url)
        response.raise_for_status()
        
        print(f"✅ Download complete!")
        print(f"📊 Response status: {response.status_code}")
        print(f"📏 CSV size: {len(response.text)} bytes")
        print(f"📝 First 200 chars of CSV:")
        print(f"{'-'*40}")
        print(response.text[:200])
        print(f"{'-'*40}")
        
        # Step 2: Parse CSV
        reader = csv.reader(response.text.splitlines())
        rows = list(reader)
        print(f"📊 Total rows in CSV: {len(rows)}")
        
        # Step 3: Extract metadata
        tournament_title = rows[1][0] if len(rows) > 1 else "Chess Tournament"
        round_info = rows[2][0] if len(rows) > 2 else "Round 1"
        
        print(f"🏆 Tournament: {tournament_title}")
        print(f"🔄 Round: {round_info}")
        
        # Step 4: Parse pairings
        pairings = []
        print(f"🔎 Parsing pairings from row 4 onward...")
        
        for i, row in enumerate(rows[3:], start=4):
            if len(row) >= 5 and row[0] and row[0].strip().isdigit():
                
                # Get results independently
                white_result = row[1].strip().upper() if len(row) > 1 else ''
                black_result = row[3].strip().upper() if len(row) > 3 else ''
                
                # Validate results
                valid_results = ['W', 'L', 'D', 'X', 'F', '']
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
                }
                
                if pairing['white_player'] or pairing['black_player']:
                    pairings.append(pairing)
                    
                    # Debug first 3 pairings
                    if len(pairings) <= 3:
                        print(f"  📋 Sample pairing {len(pairings)}: Board {pairing['board']} - {pairing['white_player']} vs {pairing['black_player']} ({pairing['white_result']}/{pairing['black_result']})")
        
        print(f"✅ Found {len(pairings)} pairings for {section_name}")
        
        return {
            'tournament': tournament_title,
            'round': round_info,
            'last_updated': datetime.now().isoformat(),
            'section': section_name,
            'pairings': pairings
        }
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to update all sections"""
    
    print(f"\n{'⭐'*10} CHESS TOURNAMENT DATA UPDATER {'⭐'*10}")
    print(f"🕐 Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'⭐'*50}\n")
    
    # Create output directory
    os.makedirs('public/data', exist_ok=True)
    print(f"📁 Output directory: {os.path.abspath('public/data')}")
    
    # Check if directory exists and is writable
    if os.path.exists('public/data'):
        print(f"✅ Directory exists and is writable")
        # List existing files
        existing_files = os.listdir('public/data')
        print(f"📄 Existing files: {existing_files if existing_files else 'None'}")
    else:
        print(f"❌ Failed to create directory")
    
    # Process all sections
    all_data = {}
    total_pairings = 0
    
    for section_name, url in SECTIONS.items():
        print(f"\n{'➖'*40}")
        section_data = fetch_and_transform(section_name, url)
        
        if section_data:
            all_data[section_name] = section_data
            section_pairings = len(section_data['pairings'])
            total_pairings += section_pairings
            
            # Save individual section file
            filename = f'public/data/{section_name}_pairings.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(section_data, f, indent=2, ensure_ascii=False)
            
            # Verify file was saved
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"💾 Saved {filename} ({file_size} bytes, {section_pairings} pairings)")
            else:
                print(f"❌ Failed to save {filename}")
    
    # Save combined data
    if all_data:
        combined_file = 'public/data/all_pairings.json'
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        if os.path.exists(combined_file):
            combined_size = os.path.getsize(combined_file)
            print(f"\n💾 Saved combined file: {combined_file} ({combined_size} bytes)")
    
    # Summary
    print(f"\n{'⭐'*50}")
    print(f"✅ UPDATE COMPLETE!")
    print(f"📊 Summary:")
    print(f"   - Sections processed: {', '.join(SECTIONS.keys())}")
    print(f"   - Total pairings: {total_pairings}")
    print(f"   - Files saved in: public/data/")
    print(f"   - End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # List final files
    final_files = os.listdir('public/data')
    print(f"\n📄 Final files in public/data/:")
    for file in sorted(final_files):
        file_size = os.path.getsize(f'public/data/{file}')
        print(f"   - {file} ({file_size} bytes)")
    
    print(f"{'⭐'*50}\n")

if __name__ == "__main__":
    main()