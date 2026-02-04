import csv
import argparse
import os

def clean_data(input_file, output_file, threshold=None):
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    print(f"Reading from {input_file}...")
    print(f"Filtering for fetch_status='success'...")
    if threshold is not None:
        print(f"Applying confidence threshold: {threshold}")
    else:
        print("No confidence threshold applied.")

    processed_rows = []
    headers = []

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        total_count = 0
        success_count = 0
        
        for row in reader:
            total_count += 1
            
            # 1. Filter by fetch_status
            if row.get('fetch_status') != 'success':
                continue
                
            success_count += 1
            
            cleaned_row = row.copy()
            
            # 2. Process Factors F01-F15
            for i in range(1, 16):
                fid = f"F{i:02d}"
                score_key = f"{fid}_score"
                
                # Get current boolean string
                raw_val = row.get(fid, 'False')
                # Parse boolean
                is_present = (raw_val == 'True')
                
                # Get score (default to 1.0 if missing, though dataset should have it)
                try:
                    score = float(row.get(score_key, 0.0))
                except ValueError:
                    score = 0.0
                
                # 3. Apply Threshold if set
                # Only strictly apply to 'True' values. If it's False, it stays False.
                if is_present and threshold is not None:
                    if score < threshold:
                        is_present = False
                
                # Encode as 1 or 0
                cleaned_row[fid] = 1 if is_present else 0
                
            processed_rows.append(cleaned_row)

    print(f"Processed {total_count} rows. Kept {success_count} successful fetches.")

    # Write output
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(processed_rows)
        print(f"Cleaned data saved to {output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and encode analysis dataset.")
    parser.add_argument('--input', default='analysis_dataset.csv', help="Input raw CSV file.")
    parser.add_argument('--output', default='analysis_dataset_cleaned.csv', help="Output cleaned CSV file.")
    parser.add_argument('--threshold', type=float, help="Confidence threshold (0.0 - 1.0). If score < threshold, treat factor as 0.")
    
    args = parser.parse_args()
    
    clean_data(args.input, args.output, args.threshold)
