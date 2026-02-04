import os
import json
import csv
import argparse
import glob
from typing import List, Dict, Any

def parse_json_file(filepath: str, is_cited: int) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('meta', {})
    factors = data.get('factors', [])

    row = {
        'url': meta.get('url', ''),
        'is_cited': is_cited,
        'fetch_status': meta.get('fetch_status', 'unknown'),
        'language': meta.get('language', 'unknown')
    }

    # Initialize all factors to False/0 initially (or handle missing)
    # Based on the schema, factors range F01 to F15.
    for i in range(1, 16):
        fid = f"F{i:02d}"
        row[fid] = False
        row[f"{fid}_score"] = 0.0

    for factor in factors:
        fid = factor.get('id')
        present = factor.get('present', False)
        score = factor.get('confidence_score', 0.0)
        
        # We only care about expected factors F01-F15 which are already initialized keys in row
        # But we need to use the fid from JSON to map correctly if it matches
        if fid in row:
            row[fid] = present
            row[f"{fid}_score"] = score

    return row

def main():
    parser = argparse.ArgumentParser(description="Compile agent results into a CSV for analysis.")
    parser.add_argument('--cited-dir', help="Directory containing JSON results for cited URLs")
    parser.add_argument('--uncited-dir', help="Directory containing JSON results for uncited URLs")
    parser.add_argument('--output', default='analysis_dataset.csv', help="Output CSV file path")
    
    args = parser.parse_args()

    rows = []

    # Process Cited
    if args.cited_dir and os.path.exists(args.cited_dir):
        files = glob.glob(os.path.join(args.cited_dir, "*.json"))
        print(f"Found {len(files)} files in cited directory: {args.cited_dir}")
        for filepath in files:
            try:
                row = parse_json_file(filepath, is_cited=1)
                rows.append(row)
            except Exception as e:
                print(f"Error parsing {filepath}: {e}")
    else:
        if args.cited_dir:
            print(f"Warning: Cited directory not found: {args.cited_dir}")

    # Process Uncited
    if args.uncited_dir and os.path.exists(args.uncited_dir):
        files = glob.glob(os.path.join(args.uncited_dir, "*.json"))
        print(f"Found {len(files)} files in uncited directory: {args.uncited_dir}")
        for filepath in files:
            try:
                row = parse_json_file(filepath, is_cited=0)
                rows.append(row)
            except Exception as e:
                print(f"Error parsing {filepath}: {e}")
    else:
        if args.uncited_dir:
            print(f"Warning: Uncited directory not found: {args.uncited_dir}")

    if not rows:
        print("No data collected. Exiting.")
        return

    # Define CSV headers
    # Fixed headers + sorted Factor keys + Score keys
    headers = ['url', 'is_cited', 'fetch_status', 'language']
    for i in range(1, 16):
        fid = f"F{i:02d}"
        headers.append(fid)
        headers.append(f"{fid}_score")

    try:
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                # Ensure row only contains known headers (though DictWriter handles extras efficiently? No, it raises ValueError if extras='raise', defaults to ignoring if extrasaction='ignore'. But we want to be clean).
                # Just passing the row is fine as long as keys match fieldnames.
                writer.writerow(row)
        print(f"Successfully wrote {len(rows)} rows to {args.output}")
    except Exception as e:
        print(f"Error writing CSV: {e}")

if __name__ == "__main__":
    main()
