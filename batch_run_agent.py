import asyncio
import csv
import os
import glob
import argparse
import json
from urllib.parse import urlparse, urlunparse
from extract_features_with_agent import main as run_agent_single

# Configuration
DEFAULT_OUTPUT_DIR = 'agent_results'
MAX_CONCURRENT_REQUESTS = 50

def normalize_url(url):
    """
    Normalizes a URL by lowercasing scheme/netloc, removing trailing slash, and removing fragments.
    Also handles URLs missing a scheme by assuming https://.
    """
    try:
        url = url.strip()
        # If no scheme, assume https
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        parsed = urlparse(url)
        
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip('/')
        
        # Reconstruct WITHOUT fragment
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ''))
    except Exception:
        return url.strip().lower()

def get_safe_filename_prefix(url):
    """Replicate the sanitization logic from the agent script to check for existing files."""
    safe_url = "".join([c for c in url if c.isalnum() or c in ('-', '_')]).strip()[:100]
    return safe_url

async def process_url(sem, url, row_idx, output_dir):
    async with sem:
        # Check if already processed
        safe_prefix = get_safe_filename_prefix(url)
        # Look for files starting with this prefix in output dir
        existing = glob.glob(os.path.join(output_dir, f"{safe_prefix}_*.json"))
        
        is_processed = False
        normalized_target_url = normalize_url(url)

        if existing:
            # Check content of existing files to deal with prefix collisions
            for fpath in existing:
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Check meta.url
                        file_url = data.get('meta', {}).get('url')
                        if file_url:
                            if normalize_url(file_url) == normalized_target_url:
                                is_processed = True
                                break
                except Exception:
                    # If file is unreadable or bad JSON, ignore it (don't count as processed)
                    pass

        if is_processed:
            print(f"[{row_idx}] Skipping {url} (already processed)")
            return
        
        print(f"[{row_idx}] Processing {url}...")
        try:
            await run_agent_single(url, output_dir=output_dir)
        except Exception as e:
            print(f"[{row_idx}] Error processing {url}: {e}")

async def batch_main(input_csv, output_dir, limit=None):
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found.")
        return

    urls = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if 'url' in row and row['url'].strip():
                urls.append((i + 1, row['url'].strip()))

    print(f"Found {len(urls)} URLs in {input_csv}.")
    
    if limit:
        print(f"Limiting to first {limit} URLs.")
        urls = urls[:limit]

    print(f"Output directory: {output_dir}")
    
    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = []
    for idx, url in urls:
        tasks.append(process_url(sem, url, idx, output_dir))
    
    await asyncio.gather(*tasks)
    print("Batch processing complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch run agent on URLs from a CSV file.")
    parser.add_argument("input_csv", help="Path to the input CSV file containing URLs.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory to save the results.")
    parser.add_argument("--limit", type=int, help="Limit processing to the first N URLs.")
    args = parser.parse_args()

    try:
        asyncio.run(batch_main(args.input_csv, args.output_dir, args.limit))
    except KeyboardInterrupt:
        print("\nBatch processing interrupted.")
