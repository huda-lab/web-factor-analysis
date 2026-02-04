import csv
import os
from urllib.parse import urlparse, urlunparse

# Input and output files
INPUT_FILE = 'uncited_in_cited_conversations.csv'
OUTPUT_FILE = 'filtered_uncited_urls.csv'

# Exclusion criteria
EXCLUDED_EXTENSIONS = {
    '.pdf', '.jpg', '.png', '.gif', '.jpeg', 
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
    '.zip', '.rar', '.mp3', '.mp4', '.avi'
}

# EXCLUDED_DOMAINS = {
#     'facebook.com', 'instagram.com', 'twitter.com', 'x.com', 
#     'reddit.com', 'youtube.com', 'vimeo.com', 'tiktok.com', 
#     'linkedin.com', 'amazon.com', 
#     'docs.google.com', 'drive.google.com', 'sheets.google.com', 'slides.google.com', 
#     'notion.so',
#     'wikipedia.org',
#     'scribd.com',
#     'pinterest.com'

# }

EXCLUDED_DOMAINS = {
    'youtube.com', 'vimeo.com', 'tiktok.com', 
    'docs.google.com', 'drive.google.com', 'sheets.google.com', 'slides.google.com', 
    'notion.so',
    'scribd.com',
    'pinterest.com'
}

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

def is_substantial_content(url):
    """
    Checks if a URL represents substantial web content based on exclusion rules.
    """
    try:
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        netloc = parsed_url.netloc.lower()
        
        # 1. Check File Extensions
        for ext in EXCLUDED_EXTENSIONS:
            if path.endswith(ext):
                return False, f"Extension: {ext}"
        
        # 2. Check Domains (checking if the netloc ends with the excluded domain to catch subdomains)
        # Handle 'www.' prefix if present in netloc for cleaner matching, though endswith works well.
        # We explicitly want to catch 'en.wikipedia.org' with 'wikipedia.org'
        for domain in EXCLUDED_DOMAINS:
            if netloc == domain or netloc.endswith('.' + domain):
                return False, f"Domain: {domain}"
                
        return True, "OK"
        
    except Exception as e:
        print(f"Error parsing URL {url}: {e}")
        return False, "Error"

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return

    kept_urls = []
    removed_count = 0
    removal_reasons = {}

    print(f"Reading from {INPUT_FILE}...")
    
    seen_urls = set()

    with open(INPUT_FILE, 'r', encoding='utf-8', newline='') as infile:
        reader = csv.reader(infile)
        try:
            # Check if there's a header. The previous files had headers: conversation_id, title, url
            # We'll read the first row and check.
            first_row = next(reader)
            # If the first row looks like a header, keep it.
            if first_row and 'conversation_id' in first_row[0].lower():
                header = first_row
            else:
                header = ['conversation_id', 'title', 'url'] # Default if missing
                # Reset reader if it wasn't a header? 
                # Actually, based on previous context, the files created had headers.
                # Let's assume headers exist.
                pass 
                
        except StopIteration:
            print("Input file is empty.")
            return

        # Process rows
        for row in reader:
            if not row: continue
            
            # Assuming URL is the 3rd column (index 2) based on previous turn's grep commands
            if len(row) >= 3:
                url = row[2]
                
                normalized = normalize_url(url)
                if normalized in seen_urls:
                    continue
                
                is_substantial, reason = is_substantial_content(url)
                
                if is_substantial:
                    kept_urls.append(row)
                    seen_urls.add(normalized)
                else:
                    removed_count += 1
                    # Track reasons for summary
                    base_reason = reason.split(':')[0] if ':' in reason else reason
                    # detailed reason
                    specific_reason = reason
                    removal_reasons[specific_reason] = removal_reasons.get(specific_reason, 0) + 1

    # Write output
    print(f"Writing {len(kept_urls)} URLs to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(kept_urls)

    print("-" * 30)
    print("Filtering Complete.")
    print(f"Total processed: {len(kept_urls) + removed_count}")
    print(f"Removed: {removed_count}")
    print(f"Remaining: {len(kept_urls)}")
    print("-" * 30)
    print("Top removal reasons:")
    # Sort reasons by count
    sorted_reasons = sorted(removal_reasons.items(), key=lambda x: x[1], reverse=True)
    for reason, count in sorted_reasons[:20]:
        print(f"  {reason}: {count}")

if __name__ == "__main__":
    main()
