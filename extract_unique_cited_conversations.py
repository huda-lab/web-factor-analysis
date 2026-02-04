import pandas as pd
import os

def main():
    input_file = 'cited_urls.csv'
    output_file = 'unique_cited_conversations.csv'

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    try:
        df = pd.read_csv(input_file)
        
        # Check for required columns
        required_columns = ['conversation_id', 'title']
        if not all(col in df.columns for col in required_columns):
            print(f"Error: Input file must contain columns: {required_columns}")
            return

        # Extract unique conversations
        unique_conversations = df[required_columns].drop_duplicates(subset=['conversation_id'])
        
        # Save to CSV
        unique_conversations.to_csv(output_file, index=False)
        
        print(f"Processed {len(df)} rows.")
        print(f"Found {len(unique_conversations)} unique conversations.")
        print(f"Saved results to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
