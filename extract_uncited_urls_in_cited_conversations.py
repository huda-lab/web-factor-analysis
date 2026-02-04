import csv

def main():
    cited_conversations_file = 'cited_conversations.csv'
    uncited_urls_file = 'uncited_urls.csv'
    output_file = 'uncited_in_cited_conversations.csv'
    
    cited_conversation_ids = set()
    
    print("Reading cited conversation IDs...")
    try:
        with open(cited_conversations_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'conversation_id' in row and row['conversation_id']:
                    cited_conversation_ids.add(row['conversation_id'])
        print(f"Found {len(cited_conversation_ids)} unique cited conversations.")
    except FileNotFoundError:
        print(f"Error: {cited_conversations_file} not found. Please ensure it exists.")
        return

    filtered_rows = []
    
    print("Filtering uncited URLs...")
    try:
        with open(uncited_urls_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                if row['conversation_id'] in cited_conversation_ids:
                    filtered_rows.append(row)
                    
        print(f"Found {len(filtered_rows)} uncited URLs belonging to cited conversations.")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_rows)
            
        print(f"Successfully wrote filtered URLs to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: {uncited_urls_file} not found.")

if __name__ == "__main__":
    main()
