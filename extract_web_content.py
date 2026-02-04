import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import logging
import argparse
import concurrent.futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extraction.log"),
        logging.StreamHandler()
    ]
)

def extract_content(url):
    """
    Extracts text content from a given URL.
    Returns the title and the body text.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else "No Title"
        
        # Remove unwanted elements
        # Removing scripts, styles, navigation, footers, headers, and meta tags
        for element in soup(["script", "style", "nav", "footer", "header", "meta", "noscript", "iframe"]):
            element.decompose()
            
        # Extract text
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return {
            'title': title.strip(),
            'text': clean_text,
            'status': 'success'
        }
        
    except requests.Timeout:
        return {'status': 'error', 'message': 'Timeout'}
    except requests.RequestException as e:
        return {'status': 'error', 'message': str(e)}
    except Exception as e:
        return {'status': 'error', 'message': f"Processing error: {str(e)}"}
def process_single_url(args):
    """
    Helper function to process a single URL result within a thread.
    args: (index, row, output_dir)
    """
    i, row, output_dir = args
    url = row['url']
    conversation_id = row['conversation_id']
    
    # Create a safe filename using conversation_id and index to ensure uniqueness
    safe_id = "".join([c for c in conversation_id if c.isalnum() or c in ('-','_')])
    output_filename = os.path.join(output_dir, f"{safe_id}_{i}.txt")
    
    # Skip if already exists (resume capability)
    if os.path.exists(output_filename):
        return
        
    logging.info(f"Processing ({i}): {url}")
    
    result = extract_content(url)
    
    if result['status'] == 'success':
        try:
            with open(output_filename, 'w', encoding='utf-8') as out:
                out.write(f"URL: {url}\n")
                out.write(f"TITLE: {result.get('title', '')}\n")
                out.write("-" * 50 + "\n")
                out.write(result.get('text', ''))
        except Exception as e:
             logging.error(f"Error writing to file {output_filename}: {e}")
    else:
        logging.error(f"Failed {url}: {result.get('message')}")

def process_csv(input_file, output_dir, max_workers=10):
    """
    Reads URLs from csv, extracts content using parallel threads.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    tasks = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Convert to list to iterate safely outside file context if needed, 
        # or just iterate and create tasks.
        # Since we just need the data, list comprehension is fine for reasonable file sizes.
        rows = list(reader)
        
    print(f"Found {len(rows)} URLs to process. Starting execution with {max_workers} workers...")
    
    # Create tuples of arguments for the worker function
    work_items = [(i, row, output_dir) for i, row in enumerate(rows)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # We use map to submit all tasks. 
        # Note: map returns an iterator of results in order. 
        # Since process_single_url doesn't return anything useful, we just consume it execution.
        list(executor.map(process_single_url, work_items))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract text content from web pages listed in a CSV file.')
    parser.add_argument('input_csv', nargs='?', help='Path to the input CSV file containing URLs')
    parser.add_argument('output_dir', nargs='?', help='Directory to save extracted text files')
    parser.add_argument('--test', help='Test extraction on a single URL', default=None)
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers (default: 10)')

    args = parser.parse_args()

    if args.test:
        test_url = args.test
        print(f"Testing extraction on {test_url}...")
        result = extract_content(test_url)
        print("Title:", result.get('title'))
        print("Content Preview:\n", result.get('text')[:500])
    
    elif args.input_csv and args.output_dir:
        print(f"Starting batch processing from {args.input_csv} to {args.output_dir}...")
        process_csv(args.input_csv, args.output_dir, max_workers=args.workers)
        print("Batch processing complete.")
    
    else:
        # Default behavior if no args provided (keep backwards compatibility or show help)
        parser.print_help()
        print("\nExample usage:")
        print("  python3 extract_web_content.py filtered_uncited_urls.csv conversations_content")
        print("  python3 extract_web_content.py --test https://example.com")
